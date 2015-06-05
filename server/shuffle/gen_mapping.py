import sys, os
import random
import math
import glob
import shutil

action_map = 'map'
action_demap = 'demap'




def shuffler(t_indexp1_list, t_N, t_seed, t_wlen, t_action=None):
    mapped_index_list = []
    N_windows = int(math.ceil(float(t_N)/t_wlen))
    if seed is not None:
        random.seed(t_seed)
    random_shifters = random.sample(xrange(N_windows), N_windows)

    for t_indexp1 in t_indexp1_list:
        t_index = t_indexp1 - 1
        k_window = int(t_index/t_wlen)
        if k_window == (N_windows - 1): # Last window do nothing
            mapped_index_list.append(t_indexp1)
            continue

        window_head = k_window*t_wlen
        if (t_action is None) or (t_action == action_map):
            mapped_index = ((t_index - window_head) + random_shifters[k_window])%t_wlen + window_head
        else:
            mapped_index = ((t_index - window_head) - random_shifters[k_window])%t_wlen + window_head

        mapped_index_list.append(mapped_index + 1)
        

    return mapped_index_list


if __name__ == "__main__":
    N_mapfiles = 5

    this_file_path = os.path.dirname(os.path.abspath(__file__))
    seed = None #random.randint(1, 2015)
    test_images_dir_wildcard = '../images/*.*'
    if len(sys.argv) > 1:
        print sys.argv[1] + "(Input within quotes)"
        test_images_dir_wildcard = sys.argv[1]

    test_images_dir_wildcard = os.path.join(this_file_path, test_images_dir_wildcard)
    N_images = len(glob.glob(test_images_dir_wildcard))
    print "Found {} images in directory {}".format(N_images, test_images_dir_wildcard)
    window_len = 5
    input_index = list(range(1, N_images+1))

    list_of_images = glob.glob(test_images_dir_wildcard)


    for k_mapfile in range(1, N_mapfiles+1):
        mapped_index = shuffler(input_index, N_images, seed, window_len, action_map)

        # Write to a map file
        map_file = "map"+str(k_mapfile)+".txt"
        with open(map_file, 'wb') as f:
            for s in mapped_index:
                f.write(str(s) + '\n')

        # Create directory and copy images
        map_dir_local = "map"+str(k_mapfile)
        map_dir = os.path.join(this_file_path, map_dir_local)
        os.makedirs(map_dir)
        # copy images
        for k in range(0, N_images):
            src_file = os.path.join(test_images_dir_wildcard, list_of_images[k])
            dst_file = os.path.join(map_dir, str(mapped_index[k])+".jpg")
            shutil.copy2(src_file, dst_file)
    
    sys.exit()
