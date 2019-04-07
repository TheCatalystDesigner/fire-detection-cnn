################################################################################

# Example : perform conversion of inceptionV1OnFire tflearn model to TensorFlow protocol
# buffer (.pb) format files (for import into other tools, example OpenCV DNN)

# Copyright (c) 2019 Toby Breckon, Durham University, UK

# License : https://github.com/tobybreckon/fire-detection-cnn/blob/master/LICENSE

# Acknowledgements: some portions - tensorflow tutorial examples and URL below

################################################################################

import glob,os

################################################################################

# import tensorflow api

import tensorflow as tf
from tensorflow.python.framework import graph_util
from tensorflow.python.framework.graph_util import convert_variables_to_constants
from tensorflow.tools.graph_transforms import TransformGraph
from tensorflow.python.tools import optimize_for_inference_lib

################################################################################

# import tflearn api

import tflearn
from tflearn.layers.core import *
from tflearn.layers.conv import *
from tflearn.layers.normalization import *
from tflearn.layers.estimator import regression

################################################################################

# import opencv

import cv2

################################################################################

from inceptionV1OnFire import construct_inceptionv1onfire

################################################################################

verbose = True; # set to true to output all layer names and logs for tensorboard

################################################################################

if __name__ == '__main__':

    # construct and re-export model (so that is excludes the training layers)

    model = construct_inceptionv1onfire (224, 224, True)
    print("[INFO] Constructed InceptionV1-OnFire ...")

    model.load("models/InceptionV1-OnFire/inceptiononv1onfire",weights_only=True)
    print("[INFO] Loaded CNN network weights for inceptionV1OnFire ...")

    print("[INFO] Re-export inceptionV1-OnFire model ...")
    del tf.get_collection_ref(tf.GraphKeys.TRAIN_OPS)[:]
    model.save("inceptionv1onfire-tmp.tfl")

    # taken from: https://stackoverflow.com/questions/34343259/is-there-an-example-on-how-to-generate-protobuf-files-holding-trained-tensorflow

    print("[INFO] Import InceptionV1-OnFire model ...")

    input_checkpoint = "inceptionv1onfire-tmp.tfl"
    saver = tf.train.import_meta_graph(input_checkpoint + '.meta', True)
    sess = tf.Session();
    saver.restore(sess, input_checkpoint)

    # print out all layers to find name of output

    if (verbose):
        op = sess.graph.get_operations()
        [print(m.values()) for m in op][1]

    print("[INFO] Freeze InceptionV1-OnFire model to inceptionv1onfire.pb ...")

    # freeze and removes nodes whichFalse are not related to feedforward prediction

    minimal_graph = convert_variables_to_constants(sess, sess.graph_def, ["FullyConnected/Softmax"])

    inp_node = 'InputData/X'                   # input layer of inceptionv1onfire
    out_node = 'FullyConnected/Softmax'      # output layer of inceptionv1onfire
    graph_def = optimize_for_inference_lib.optimize_for_inference(minimal_graph, [inp_node], [out_node], tf.float32.as_datatype_enum)
    graph_def = TransformGraph(graph_def, [inp_node], [out_node], ["sort_by_execution_order"])
    with tf.gfile.FastGFile('inceptionv1onfire.pb', 'wb') as f:
        f.write(graph_def.SerializeToString())

    # write model to logs dir so we can visualize it as:
    # tensorboard --logdir="logs"

    if (verbose):
        writer = tf.summary.FileWriter('logs', graph_def)
        writer.close()

    # tidy up tmp files

    for f in glob.glob("inceptionv1onfire-tmp.tfl*"):
        os.remove(f)

    os.remove('checkpoint')

    ##############################

    # perform test inference using OpenCV

    print("[INFO] test inceptionV1OnFire model inceptionv1onfire.pb with OpenCV ...")

    # Load a model imported from Tensorflow

    tensorflowNet = cv2.dnn.readNetFromTensorflow('inceptionv1onfire.pb');

    # Input image

    img = cv2.imread('images/slic-stages.png')
    img = img[0:600,0:396]; # extract left part of example containing fire

    # Use the given image as input, which needs to be blob(s).
    tensorflowNet.setInput(cv2.dnn.blobFromImage(img, size=(224, 224), swapRB=False, crop=False))

    # Runs a forward pass to compute the net output
    networkOutput = tensorflowNet.forward()
    print("[INFO] example image - Fire: " + str(networkOutput[0][0]) + " Not Fire: " + str(networkOutput[0][1]))
    print("[INFO] - press any key to exit")

    # Show the image with a rectagle surrounding the detected objects
    cv2.imshow('Example Detection', img)
    cv2.waitKey()
    cv2.destroyAllWindows()

################################################################################
