"""
This is an python implementation of online evaluating detection results.
"""

from collections import OrderedDict
from copy import deepcopy
import numpy as np
import os
from sets import Set
import scipy.io
import sys

class DetectionEvaluate(object):
  """A class for evaluating detection results.
  """

  def __init__(self, det_meta_file, det_eval_file, det_gt_file,
      det_blacklist_file=[]):
    """Return an evaluation object who loads the "meta" data.

    det_meta_file: contains information about the synsets.
    det_eval_file: contains a list of image ids to evaluate on.
    det_gt_file: contains the ground truth for detection.
    det_blacklist_file: contains a list of image ids to be ignored.
    """

    # Load det_meta_file.
    if not os.path.exists(det_meta_file):
      print "{} does not exist!".format(det_meta_file)
      sys.exit()
    det_meta = scipy.io.loadmat(det_meta_file)
    self.wnid_label = dict()
    for synset in det_meta["synsets"][0]:
      label = int(synset[0][0][0])
      wnid = synset[1][0]
      self.wnid_label[wnid] = label

    # Load det_eval_file.
    if not os.path.exists(det_eval_file):
      print "{} does not exist!".format(det_eval_file)
      sys.exit()
    self.image_ids = dict()
    with open(det_eval_file, "r") as f:
      for line in f.readlines():
        image_name, image_id = line.rstrip("\n").split(" ")
        image_id = int(image_id)
        assert image_id not in self.image_ids
        self.image_ids[image_id] = image_name
      f.close()

    # Load blacklist_file.
    self.blacklist_id_labels = dict()
    if os.path.exists(det_blacklist_file):
      with open(det_blacklist_file, "r") as f:
        for line in f.readlines():
          image_id, wnid = line.rstrip("\n").split(" ")
          image_id = int(image_id)
          assert wnid in self.wnid_label
          label = self.wnid_label[wnid]
          if image_id not in self.blacklist_id_labels:
            self.blacklist_id_labels[image_id] = [label]
          else:
            self.blacklist_id_labels[image_id].extend([label])
      f.close()

    # Load det_gt_file.
    if not os.path.exists(det_gt_file):
      print "{} does not exist!".format(det_gt_file)
      sys.exit()
    det_gt = scipy.io.loadmat(det_gt_file)
    # Exclude blacklist image labels.
    self.num_pos_per_class = det_gt["num_pos_per_class"][0]
    # Convert to pythonic format.
    gt_img_ids = det_gt["gt_img_ids"]
    gt_obj_labels = det_gt["gt_obj_labels"][0]
    gt_obj_bboxes = det_gt["gt_obj_bboxes"][0]
    gt_obj_thr = det_gt["gt_obj_thr"][0]
    num_gt = len(gt_img_ids)
    assert len(gt_obj_labels) == num_gt
    assert len(gt_obj_bboxes) == num_gt
    assert len(gt_obj_thr) == num_gt
    self.gt_bboxes = OrderedDict()
    for i in xrange(0, num_gt):
      gt_img_id = gt_img_ids[i][0]
      gt_obj_label = gt_obj_labels[i][0]
      gt_obj_bbox = np.transpose(gt_obj_bboxes[i])
      gt_thr = gt_obj_thr[i][0]
      num_obj = len(gt_obj_label)
      assert num_obj == len(gt_obj_bbox)
      assert num_obj == len(gt_thr)
      blacklist_labels = []
      if i+1 in self.blacklist_id_labels:
        blacklist_labels = self.blacklist_id_labels[i+1]
      gt_bbox = dict()
      gt_bbox["label"] = []
      gt_bbox["bbox"] = []
      gt_bbox["threshold"] = []
      for j in xrange(0, num_obj):
        gt_label = gt_obj_label[j]
        gt_bbox["label"].append(gt_label)
        gt_bbox["bbox"].append(gt_obj_bbox[j])
        gt_bbox["threshold"].append(gt_thr[j])
        if gt_label in blacklist_labels:
          # Remove blacklist labels.
          self.num_pos_per_class[gt_label-1] -= 1
      self.gt_bboxes[gt_img_id] = gt_bbox

    # Internally store the true positive and false positive.
    self.stored_detections = dict()
    self.tps = dict()
    self.fps = dict()
    self.confidences = dict()
    self.recall = dict()
    self.precision = dict()
    self.aps = dict()
    for i in xrange(1, len(self.num_pos_per_class) + 1):
      self.aps[i] = 0.

  def evaluate(self, detections):
    """Evaluate detection results.

    detections: a dictionary which contains the detection results.
      The key is the image_id, such as [1, max_image_id].
      The value is a list of detection results for the image with format:
          [[class_id_1, confidence_1, xmin_1, ymin_1, xmax_1, ymax_1],
            ...,
            [class_id_n, confidence_n, xmin_1, ymin_1, xmax_1, ymax_1]]
    """

    # Extract detection results.
    labels = []
    for image_id, results in detections.iteritems():
      if image_id not in self.stored_detections:
        # If it is new image, store it.
        self.stored_detections[image_id] = deepcopy(results)
      else:
        # If there exists detections for the image, extend it.
        self.stored_detections[image_id].extend(deepcopy(results))
      # Evaluate current image.
      self.evaluate_one_image(image_id)
      labels.extend(self.get_detection_labels(image_id))

    # Compute updated mAP.
    labels = sorted(list(Set(labels)))
    for label in labels:
      self.aps[label] = self.compute_ap(label)
    mAP = 0.
    if len(self.aps) > 0:
      mAP = np.mean(self.aps.values())
    return mAP

  def evaluate_one_image(self, image_id):
    """Evaluate detection results for one image.

    image_id: the id of the image.
    """

    if image_id not in self.gt_bboxes:
      return
    gt_bboxes = self.gt_bboxes[image_id]
    num_gt = len(gt_bboxes["label"])
    gt_detected = np.zeros(num_gt)

    assert image_id in self.stored_detections
    detections = self.stored_detections[image_id]
    labels = []
    confidences = []
    bboxes = []
    for detection in detections:
      labels.append(detection[0])
      confidences.append(detection[1])
      bboxes.append(detection[2:])
    num_det = len(labels)
    if num_det == 0:
      return
    if num_det > 1:
      sort_idx = np.argsort(confidences)[::-1]
      labels = [labels[i] for i in sort_idx]
      bboxes = [bboxes[i] for i in sort_idx]
      confidences = [confidences[i] for i in sort_idx]

    blacklist_labels = []
    if image_id in self.blacklist_id_labels:
      blacklist_labels = self.blacklist_id_labels[image_id]

    tp = np.zeros(num_det)
    fp = np.zeros(num_det)
    for i in xrange(0, num_det):
      if labels[i] in blacklist_labels:
        continue
      bbox = bboxes[i]
      max_overlap = -1
      max_gt_idx = -1
      for j in xrange(0, num_gt):
        if labels[i] != gt_bboxes["label"][j]:
          continue
        if gt_detected[j] > 0:
          continue
        gt_bbox = gt_bboxes["bbox"][j]
        gt_threshold = gt_bboxes["threshold"][j]
        overlap = self.compute_bbox_overlap(bbox, gt_bbox)
        if overlap > gt_threshold and overlap > max_overlap:
          max_overlap = overlap
          max_gt_idx = j
      if max_gt_idx >= 0:
        tp[i] = 1
        gt_detected[max_gt_idx] = 1
      else:
        fp[i] = 1

    # Group information for different labels.
    unique_labels = Set(labels)
    for label in unique_labels:
      found_idx = [i for i, l in enumerate(labels) if l == label]
      if label not in self.tps:
        self.tps[label] = dict()
        self.fps[label] = dict()
        self.confidences[label] = dict()
      self.tps[label][image_id] = [tp[i] for i in found_idx if tp[i] != fp[i]]
      self.fps[label][image_id] = [fp[i] for i in found_idx if tp[i] != fp[i]]
      self.confidences[label][image_id] = [confidences[i] for i in found_idx if tp[i] != fp[i]]

  def compute_bbox_overlap(self, bbox1, bbox2):
    """Compute jaccard (intersection over union) overlap between two bboxes.
    """

    overlap = 0.
    inter_bbox = [max(bbox1[0], bbox2[0]), max(bbox1[1], bbox2[1]),
        min(bbox1[2], bbox2[2]), min(bbox1[3], bbox2[3])]
    inter_width = inter_bbox[2] - inter_bbox[0] + 1
    inter_height = inter_bbox[3] - inter_bbox[1] + 1
    inter_size = float(inter_width * inter_height)
    if inter_height > 0 and inter_width > 0:
      bbox1_size = (bbox1[2] - bbox1[0] + 1) * (bbox1[3] - bbox1[1] + 1)
      bbox2_size = (bbox2[2] - bbox2[0] + 1) * (bbox2[3] - bbox2[1] + 1)
      overlap = inter_size / (bbox1_size + bbox2_size - inter_size)
    return overlap

  def get_detection_labels(self, image_id):
    """Get detection labels for one image.

    image_id: the id of the image.
    """

    detections = self.stored_detections[image_id]
    labels = []
    for detection in detections:
      labels.append(detection[0])
    return list(Set(labels))

  def compute_ap(self, label):
    """Compute average precision from stored information.
    """

    if label not in self.tps:
      return 0.
    if label > len(self.num_pos_per_class):
      return 0.
    num_pos_per_class = self.num_pos_per_class[label-1]
    if num_pos_per_class <= 0:
      return 0.
    tps = []
    fps = []
    confidences = []
    for image_id in self.tps[label]:
      tps.extend(self.tps[label][image_id])
      assert image_id in self.fps[label]
      fps.extend(self.fps[label][image_id])
      assert image_id in self.confidences[label]
      confidences.extend(self.confidences[label][image_id])
    assert len(tps) == len(fps)
    assert len(tps) == len(confidences)

    # Sort based on confidences.
    sort_idx = np.argsort(confidences)[::-1]
    tps = [tps[i] for i in sort_idx]
    fps = [fps[i] for i in sort_idx]
    tps = np.asarray(tps)
    fps = np.asarray(fps)

    # Compute precision and recall.
    tps = np.cumsum(tps, dtype=float)
    fps = np.cumsum(fps, dtype=float)
    recall = tps / num_pos_per_class
    precision = tps / (tps + fps)
    # Store a copy internally.
    self.recall[label] = recall
    self.precision[label] = precision

    # Compute average precision.
    mrec = np.insert(np.insert(recall, 0, 0), -1, 1)
    mpre = np.insert(np.insert(precision, 0, 0), -1, 0)
    for i in xrange(mrec.size - 2, -1, -1):
      mpre[i] = max(mpre[i], mpre[i+1])
    ap = 0.
    for i in xrange(0, mrec.size - 1):
      if mrec[i+1] != mrec[i]:
        ap += (mrec[i+1] - mrec[i]) * mpre[i+1]
    return ap
