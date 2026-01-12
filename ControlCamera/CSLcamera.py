"""
  
  Copyright (C) 2023 Sony Computer Science Laboratories
  
  Author(s) Aliénor Lahlou
  
  free software: you can redistribute it and/or modify
  it under the terms of the GNU General Public License as published by
  the Free Software Foundation, either version 3 of the License, or
  (at your option) any later version.
  
  This program is distributed in the hope that it will be useful, but
  WITHOUT ANY WARRANTY; without even the implied warranty of
  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
  General Public License for more details.
  
  You should have received a copy of the GNU General Public License
  along with this program.  If not, see
  <http://www.gnu.org/licenses/>.
  
  #source https://github.com/mightenyip/neuronDetection/blob/14d64c44ab4a9e11af14c15961cd5ea4d22506e2/live_neuron_detection.py

"""
import pymmcore_plus
from pymmcore_plus import CMMCorePlus
import os.path
import time
import numpy as np
import matplotlib.pyplot as plt
import cv2
from PIL import Image
import json
import threading
import skimage
import ipdb
import copy
import pandas as pd
import tifffile
import os
from skimage.transform import resize
import logging

logger = logging.getLogger(__name__)


def clip(input_image, high = 99.99, low = 0.001):
    """
    Clip the input image based on the specified high and low percentiles.

    Args:
        input_image (numpy.ndarray): The input image.
        high (float): The high percentile value for clipping (default: 99.99).
        low (float): The low percentile value for clipping (default: 0.001).

    Returns:
        numpy.ndarray: The clipped image.
    """
    im = copy.copy(input_image)
    im[im<np.percentile(im, low)]=np.percentile(im, low)
    im[im>np.percentile(im, high)]=np.percentile(im, high)
    return im



class ControlCamera(threading.Thread):


    def __init__(self, config_file, cam_param, downscale=3, mm_dir = "C:/Program Files/Micro-Manager-2.0/"):
      """
      Initialize the ControlCamera object.

      Args:
          config_file (str): The path to the configuration file in JSON format.
          cam_param (dict): Additional camera parameters specified as key-value pairs.
          downscale (int): Downscale factor for video acquisition (default: 3).
          mm_dir (str): The path to the Micro-Manager installation directory (default: "C:/Program Files/Micro-Manager-2.0/").
      """
      threading.Thread.__init__(self)
      try:
        with open(config_file, "r") as f:
          config = json.load(f)
      except FileNotFoundError:
          logger.error(f"Config file '{config_file}' not found.")
          raise
      
      self.name = config["name"]
      self.video = []
      self.timing = []
      self.downscale = downscale
      self.camera_mode = "continuous_stream" #snap_image, snap_video
      self.N_im = 10

      #self.mmc = pymmcore_plus.CMMCorePlus()
      #self.mmc.getCameraDevice()
      #self.mmc.setDeviceAdapterSearchPaths([mm_dir])
      

      self.mmc = CMMCorePlus.instance()
      try:
        self.mmc.loadSystemConfiguration(config["MMconfig"])

      except:
         logger.error("Error accessing the camera with pymmcore-plus (interface with MicroManager). Consider checking that the camera driver is installed, that the .dll is known by MicroManager and that the camera is properly connected.")


      
      #basic config from config .json file
      for key in config:
        if key not in ["name", "MMconfig"]:
          try:
            self.mmc.setProperty(self.name, key, config[key])          
            logger.info(key, self.get_param(key))
          except Exception as e:
            logger.error(f"Failed to update parameter '{key}' with value '{config[key]}': {e}")             

    
      
      #local config update
      for key in cam_param:
          try:
            self.mmc.setProperty(self.name, key, cam_param[key])
            logger.info(key, self.get_param(key))

          except Exception as e:
            logger.error(f"Failed to update parameter '{key}' with value '{cam_param[key]}': {e}")             

      

    def update_param(self, key, val):
        """
        Update the camera parameter with the specified key to the given value.

        Args:
            key (str): The camera parameter key.
            val: The value to set for the camera parameter.
        """
        try:
            self.mmc.setProperty(self.name, key, val)
            logger.info(key, self.get_param(key))

        except Exception as e:
            logger.error(f"Failed to update parameter '{key}' with value '{val}': {e}")

    def get_param(self, key):
        """
        Get the current value of the camera parameter with the specified key.

        Args:
            key (str): The camera parameter key.

        Returns:
            The current value of the camera parameter.
        """
        try:
            return self.mmc.getProperty(self.name, key)
        except Exception as e:
            logger.error(f"Failed to retrieve parameter '{key}': {e}")
            return None


    def continuous_stream(self, transform=None):
      """
      Perform continuous streaming of the camera frames and display them in a window.
      """
      cv2.namedWindow('live',cv2.WINDOW_AUTOSIZE)
      self.mmc.startContinuousSequenceAcquisition(1)
      while True:
        if self.mmc.getRemainingImageCount() > 0:
          self.frame = self.mmc.popNextImage()
          self.image = np.mean(self.frame[:,:,:3], axis =2)
          #self.image = np.array(Image.fromarray(np.uint8(self.frame)))
          #self.image[self.image<np.quantile(self.image, 0.99)] = 0
          if transform is not None:
                # Apply the transform function here
                transformed_image = self.image.copy()
                transformed_image = transform(transformed_image)
                image = resize(self.image, transformed_image.shape)
                # Create a combined image by stacking the original and transformed images horizontally
                combined_image = np.hstack((image, transformed_image))
                # Display the combined image
                
                cv2.imshow('live', cv2.normalize(combined_image, None, 255, 0, cv2.NORM_MINMAX, cv2.CV_8UC1))
          else:
                cv2.imshow('live', cv2.normalize(self.image, None, 255,0, cv2.NORM_MINMAX, cv2.CV_8UC1))
        if cv2.waitKey(1) & 0xFF == ord('q'):
          break

      cv2.destroyAllWindows()
      self.mmc.stopSequenceAcquisition()
      
    def reset(self):
       self.mmc.reset()

    def snap_image(self):
        """
        Capture a single image from the camera.

        Returns:
            numpy.ndarray: The captured image.
        """
        try:
          self.mmc.snapImage()
          self.frame = self.mmc.getImage()
          self.image = np.array(Image.fromarray(np.uint8(self.frame)))
          return self.image
        except Exception as e:
          logger.error(f"Failed to snap image: {e}")
          return None

    def snap_video(self, N_im): 
      """
      Capture a video with the specified number of frames.

      Args:
          N_im (int): The number of frames to capture.

      Returns:
          numpy.ndarray: The captured video frames.
        """
      self.video = []
      self.timing = []
      cv2.namedWindow('live',cv2.WINDOW_AUTOSIZE)
      self.mmc.startContinuousSequenceAcquisition(1)
      i=0
      while True:
        if self.mmc.getRemainingImageCount() > 0:
          frame = self.mmc.popNextImage()
          if len(frame.shape)==3:
            frame = np.mean(frame, axis = 2)
          self.video.append(skimage.transform.downscale_local_mean(frame, self.downscale))
          self.timing.append(time.time())
          self.image = frame
          #self.image = np.array(Image.fromarray(np.uint8(frame)))

          cv2.imshow('live',  cv2.normalize(clip(self.image), None, 255,0, cv2.NORM_MINMAX, cv2.CV_8UC1))
          #
          #print(np.mean(frame))
          i+=1

        if cv2.waitKey(1) & 0xFF == ord('q'): 
          break

        if i>=N_im:
          break

      cv2.destroyAllWindows()
      self.mmc.stopSequenceAcquisition()
      self.mmc.reset()
      return self.video


    def run(self):
        """
        Run the camera based on the specified camera mode. Useful for threads.
        """
        # call the appropriate method based on a flag or some other logic
        if self.camera_mode == 'continuous_stream':
            self.continuous_stream()
        elif self.camera_mode == 'snap_video':
            self.snap_video(self.N_im)
        else:
            raise ValueError("Invalid mode: {}".format(self.camera_mode))      


    def save_video(self, save_folder,  _run=None):
        """
        Save the captured video frames to the specified folder and log the timing information.

        Args:
            save_folder (str): The path to the folder where the video and timing files will be saved.
            _run (object): The object representing the current run in the experiment logging framework (default: None).

        Returns:
            numpy.ndarray: The captured video frames.
            numpy.ndarray: The timing information for each frame.
        """        
    
        result, timing = np.array(self.video), np.array(self.timing)
        fname = save_folder + "/video.tiff"
        tifffile.imwrite(fname, result[:,:,:],photometric="minisblack")
                
        fname_t = save_folder + '/video_timing.csv'
        pd.DataFrame(timing).to_csv(fname_t)


        #ftmp = tempfile.NamedTemporaryFile(delete=False)
        #fname = ftmp.name + ".pkl"
        #with open(fname,'wb') as f:
        #    pickle.dump(result, f)

        #_run.add_artifact(fname, "video.npy")
        if _run is not None:
          _run.add_artifact(fname, "video.tiff")
          _run.add_artifact(fname, "video_timing.csv")
        return result, timing

