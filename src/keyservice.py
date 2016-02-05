#!/usr/bin/python

import sys
import argparse
import json

import glob
import time

DESCRIPTION = \
"""
Starts a background service which polls for a keyfile, then performs an action.
"""

def wait_for_key_in(key_glob,
                    key_extractor,
                    interval_secs,
                    timeout_secs=-1):
    
    start_time = time.time()    
 
    while True:
        
        key_filenames = glob.glob(key_glob)
        for key_filename in key_filenames:
            key = key_extractor(key_filename)
            if key:
                return (key, key_filename)
        
        curr_time = time.time()
        
        if timeout_secs >= 0 and curr_time - start_time > timeout_secs:
            return (None, None) 

        time.sleep(interval_secs)

def wait_for_key_out(key_filename,
                     interval_secs,
                     timeout_secs=-1):

    start_time = time.time()

    while True:

        if not os.path.exists(key_filename):
            return True

        curr_time = time.time()

        if timeout_secs >= 0 and curr_time - start_time > timeout_secs:
            return False

        time.sleep(interval_secs)

class KeyAction:

    def __init__(self):
        pass
    
    def extract_key(key_filename):
        return None

    def key_in(key):
        pass

    def key_out():
        pass 

def run_service(key_glob, action, interval_secs):
    
    while True:

        key, key_filename = \
            wait_for_key_in(key_glob, 
                            lambda key_filename: return action.extract_key(key_filename),
                            interval_secs)
        
        if not key:
            break

        action.key_in(key)

        key_removed = \
            wait_for_key_out(key_filename,
                             interval_secs)

        if not key_removed:
            break

        action.key_out()
        

if __name__ == '__main__':
    
    parser = argparse.ArgumentParser(description=DESCRIPTION) 
    
    parser.add_argument("--keyfile", dest="key_glob",
        help="Key file (or files) to look for.")
 
    parser.add_argument("--action", dest="action_filename",
        help="Configuration of the action to take when the key is added or removed.") 

    parser.add_argument("--interval", dest="interval_secs", type=int, default=1,
        help="Polling interval for the key add/remove events.")     

    args = parser.parse_args(sys.argv[1:])
    
    if not args.key_glob:
        raise Exception("A keyfile to detect must be specified.")

    if not args.action:
        raise Exception("An action configuration is required.")

    action_json = None
    with open(args.action_filename, 'r') as action_file:
        action_json = json.load(action_file)

    action_clazz_path = action_json['class'].split('.')
    action_clazz_name = action_clazz_path[-1]
    action_module_name = '.'.join(action_clazz_path[0:-1])
    
    action_module = __import__(action_module_name, fromlist=action_clazz_name)
    action_clazz = getattr(action_module, action_clazz_name)
    
    del action_json['class']
    action = action_clazz(**action_json)
    
    run_service(args.key_glob, action, args.interval_secs)  
