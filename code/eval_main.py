# Copyright 2020 Google LLC.
# SPDX-License-Identifier: Apache-2.0

import sys

def main(base_path):
    # Receives path to root dir, containing the annotated data and DA + systems scores from WMT19.
    # Calculates KoBE for all system outputs, caculcates Pearson correlation to human DA and 
    # compares it to the submitted systems.
    

if __name__ == '__main__':
    main(sys.argv[1])
