import sys, os
import random
import math
import glob
import shutil
import re
import filecmp

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
    print this_file_path
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

    # If map file
    if len(sys.argv) > 2:
        my_list_of_images = []
        my_dir = os.path.dirname(test_images_dir_wildcard)
        master_map_file = sys.argv[2]
        print master_map_file + "(Input within quotes)"
        master_map_file = os.path.join(this_file_path, master_map_file)
        with open(master_map_file, 'rb') as f:
            for line in f:
                short_name = line.split()[0]
                match = re.search("\.", short_name)
                if not match:
                    short_name += ".JPEG"
                full_name = os.path.join(my_dir, short_name)
                print full_name
                if not os.path.isfile(full_name):
                    print "Image does not exist\n"
                    sys.exit(2)
                my_list_of_images.append(full_name)

        list_of_images = my_list_of_images

    for k_mapfile in range(0, N_mapfiles+1):
        if k_mapfile == 0:
            mapped_index = input_index
        else:
            mapped_index = shuffler(input_index, N_images, seed, window_len, action_map)

        # Write to a map file
        map_file = "map"+str(k_mapfile)+".txt"
        map_file = os.path.join(this_file_path, map_file)
        with open(map_file, 'wb') as f:
            for s in mapped_index:
                f.write(str(s) + '\n')

        # Create directory and copy images
        map_dir_local = "map"+str(k_mapfile)
        map_dir = os.path.join(this_file_path, map_dir_local)
        os.makedirs(map_dir)
        # copy images
        for k in range(0, N_images):
            src_file = list_of_images[k]
            dst_file = os.path.join(map_dir, str(mapped_index[k])+".jpg")
            shutil.copy2(src_file, dst_file)


    # Cross-check
    map0_dir = os.path.join(this_file_path, "map0")
    for k_mapfile in range(1, N_mapfiles+1):
        map_file = "map"+str(k_mapfile)+".txt"
        map_file = os.path.join(this_file_path, map_file)

        map_dir_local = "map"+str(k_mapfile)
        map_dir = os.path.join(this_file_path, map_dir_local)
        tmp_dir = os.path.join(this_file_path, "tmp")
        if os.path.isdir(tmp_dir):
            shutil.rmtree(tmp_dir)
        os.makedirs(tmp_dir)

        tmp_list = []
        with open(map_file, 'rb') as f:
            for line in f:
                tmp_index = line.split()[0]
                tmp_list.append(tmp_index)

        for k in range(1, N_images+1):
            demapped_index = tmp_list.index(str(k)) + 1
            src_file = str(k)+".jpg"
            src_file = os.path.join(map_dir, src_file)

            dst_file = str(demapped_index)+".jpg"
            dst_file = os.path.join(map0_dir, dst_file)

            if not filecmp.cmp(src_file, dst_file):
                print "File mismatch \n{}\n{}".format(src_file, dst_file)
                sys.exit(2)

        print map_dir+" Verified"


        
    sys.exit()
