# -*- coding: utf-8 -*-
"""
Created on Mon Mar  7 21:31:18 2022

@author: wardc
"""
import argparse
import time



def main():

    parser = argparse.ArgumentParser(description='CCaC')
    parser.add_argument(
        '-i', help='thing to print'
        )
    
    
    
    args, others = parser.parse_known_args()
    
    for j in range(10):
        print(args.i)
        time.sleep(0.5)
        
if __name__ == '__main__':
    main()