import sys, os
import random
import math
import glob
import shutil
import csv

standard_fieldnames = ['image','class_id','confidence','xmin','ymin','xmax','ymax']


if __name__ == "__main__":
    
    this_file_path = os.path.dirname(os.path.abspath(__file__))
    result_csvfile = '../csv/submissions/lpirc.csv'
    map_file = 'map1.txt'

    result_csvfile = os.path.join(this_file_path, result_csvfile)
    map_file = os.path.join(this_file_path, map_file)

    result_dirname = os.path.dirname(result_csvfile)
    result_username = os.path.basename(result_csvfile)
    print "Result dirname = {}".format(result_dirname)
    print "Username = {}".format(result_username)

    demapped_result_dir = os.path.join(result_dirname, '../demapped_submissions')
    # Create demapped submission directory
    if not os.path.exists(demapped_result_dir):
        os.makedirs(demapped_result_dir)

    demapped_result_csvfile = os.path.join(demapped_result_dir, result_username)
    print "Creating csv file: {}".format(demapped_result_csvfile)

    # Get mapping list
    with open(map_file, 'rb') as f:
        map_list = [line.rstrip('\n') for line in f]

    # Modify image id in submission file
    demapped_rows_all = []
    with open(result_csvfile) as csvfile:
        reader = csv.DictReader(csvfile, skipinitialspace=True, fieldnames=standard_fieldnames)
        for row in reader:
            image_id = row['image'].split()[0]
            demapped_image_id = str(map_list.index(image_id)+1)

            demapped_row = []
            for fields in standard_fieldnames:
                if fields != "image":
                    demapped_row.append(row[fields].split()[0])
                else:
                    demapped_row.append(demapped_image_id)
                    print "Image id demapped"
    
            demapped_rows_all.append(demapped_row)

    with open(demapped_result_csvfile, 'wb') as fid:
        writer = csv.writer(fid)
        writer.writerows(demapped_rows_all)

    
    sys.exit()
