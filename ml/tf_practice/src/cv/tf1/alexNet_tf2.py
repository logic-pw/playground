#!/usr/bin/env python3
# -*- coding:utf8 -*-

"""
alexNet implementation, feature of alexNet is dropout, LRN(local response normalization), max pooling and relu.
dev with tf2.5
"""

import tensorflow as tf
from loader import load_data
import math
import numpy as np
import time


def lr_compute(step):
    max_lr, min_lr, decay_speed = 0.003, 0.0001, 2000.0
    return min_lr + (max_lr - min_lr) * math.exp(-step / decay_speed)


def main(argv=None):
    train_data, train_label, test_data, test_label = load_data.load_raw_cifar10()
    print("load success")
    x_in = tf.placeholder(tf.float32, shape=(None, 32, 32, 3))
    # t is label
    t = tf.placeholder(tf.float32, shape=(None, 10))
    # x = tf.reshape(x_in, [-1, 784])
    # print('--',x.get_shape().as_list())
    # w = tf.Variable(tf.zeros([784,10]))
    # b = tf.Variable(tf.zeros([10]))
    K = 32
    L = 96
    M = 128
    N = 256

    # init_op = tf.global_variables_initializer()
    # init_op = tf.initialize_all_variables()
    # y = tf.nn.softmax(tf.matmul(x, w) + b)
    p_keep = tf.placeholder(tf.float32)

    # input shape is N * 32 * 32 * 3
    w1 = tf.Variable(tf.truncated_normal([3, 3, 3, K], stddev=0.1))
    b1 = tf.Variable(tf.ones([K]) / 10)
    y1 = tf.nn.relu(tf.nn.conv2d(x_in, w1, strides=[1, 2, 2, 1], padding='SAME') + b1)
    # y1_lrn = tf.nn.lrn(y1)
    # y1d = tf.nn.dropout(y1_lrn, p_keep)
    # input shape is N * 16 * 16 * 96
    print("y5_pool.shape", y1.get_shape().as_list())
    y1_pool = tf.nn.max_pool(y1, ksize=[1, 3, 3, 1], strides=[1, 1, 1, 1], padding='SAME')

    # input shape is N * 16 * 16 * 96
    w2 = tf.Variable(tf.truncated_normal([3, 3, K, L], stddev=0.1))
    b2 = tf.Variable(tf.ones([L]) / 10)
    y2 = tf.nn.relu(tf.nn.conv2d(y1_pool, w2, strides=[1, 1, 1, 1], padding='SAME') + b2)
    # y2_lrn = tf.nn.lrn(y2)
    # y2d = tf.nn.dropout(y2_lrn, p_keep)
    y2_pool = tf.nn.max_pool(y2, ksize=[1, 3, 3, 1], strides=[1, 2, 2, 1], padding='SAME')

    # input shape is N * 8 * 8 *  256
    w3 = tf.Variable(tf.truncated_normal([3, 3, L, M], stddev=0.1))
    b3 = tf.Variable(tf.ones([M]) / 10)
    y3 = tf.nn.relu(tf.nn.conv2d(y2_pool, w3, strides=[1, 1, 1, 1], padding='SAME') + b3)
    # y3d = tf.nn.dropout(y3, p_keep)

    # input shape is N * 8 * 8 *  384
    w4 = tf.Variable(tf.truncated_normal([3, 3, M, M], stddev=0.1))
    b4 = tf.Variable(tf.ones([M]) / 10)
    y4 = tf.nn.relu(tf.nn.conv2d(y3, w4, strides=[1, 1, 1, 1], padding='SAME') + b4)
    # y3d = tf.nn.dropout(y3, p_keep)

    # input shape is N * 8 * 8 *  384
    w5 = tf.Variable(tf.truncated_normal([3, 3, M, L], stddev=0.1))
    b5 = tf.Variable(tf.ones([L]) / 10)
    y5 = tf.nn.relu(tf.nn.conv2d(y4, w5, strides=[1, 1, 1, 1], padding='SAME') + b5)
    y5_pool = tf.nn.max_pool(y5, ksize=[1, 3, 3, 1], strides=[1, 2, 2, 1], padding='SAME')
    print("y5_pool.shape", y5_pool.get_shape().as_list())

    # level 6 input shape is N , 4 * 4* 256
    w6 = tf.Variable(tf.truncated_normal([4 * 4 * L, N], stddev=0.1))
    b6 = tf.Variable(tf.ones([N]) / 10)
    y6_reshape = tf.reshape(y5_pool, shape=[-1, 4 * 4 * L])
    y6 = tf.nn.relu(tf.matmul(y6_reshape, w6) + b6)
    y6d = tf.nn.dropout(y6, p_keep)

    # level 7 input shape is N * 4096
    w7 = tf.Variable(tf.truncated_normal([N, N], stddev=0.1))
    b7 = tf.Variable(tf.ones([N]) / 10)
    y7 = tf.nn.relu(tf.matmul(y6d, w7) + b7)
    y7d = tf.nn.dropout(y7, p_keep)

    # level 8
    w8 = tf.Variable(tf.truncated_normal([N, 10], stddev=0.1))
    b8 = tf.Variable(tf.ones([10]) / 10)
    logits = tf.matmul(y7d, w8) + b8
    y = tf.nn.softmax(logits)

    cross_entropy = tf.reduce_mean(tf.nn.softmax_cross_entropy_with_logits(logits=logits, labels=t))
    is_correct = tf.equal(tf.argmax(y, 1), tf.argmax(t, 1))
    accuracy = tf.reduce_mean(tf.cast(is_correct, tf.float32))
    lr = tf.placeholder(tf.float32, shape=[])
    # optimizer = tf.train.GradientDescentOptimizer(learning_rate=0.003)
    train_step = tf.train.AdamOptimizer(lr).minimize(cross_entropy)
    batch_size = 100
    init_op = tf.initialize_all_variables()
    # print(train_data.shape)
    # print(train_label.shape)
    with tf.Session() as sess:
        # tf.initialize_all_variables().run()
        sess.run(init_op)
        for step in range(4000):
            if step % 50 == 0:
                t_now = time.time()
                start_time = int(round(t_now * 1000))
            start = (step * batch_size) % 50000
            end = start + batch_size
            batch_xs = train_data[start:end, :, :, :]
            batch_ys = train_label[start:end, :]
            # print('==', x.get_shape())
            # print('==', w.get_shape())
            # print('==', batch_xs.shape)
            sess.run(train_step, feed_dict={x_in: batch_xs, t: batch_ys, lr: lr_compute(step), p_keep: 0.5})
            # print(type(x))
            if step % 50 == 0:
                # train set metric
                acc, loss = sess.run([accuracy, cross_entropy], feed_dict={x_in: batch_xs, t: batch_ys, p_keep: 1})
                # print('train acc,loss:',acc,loss)
                test_acc, test_loss = sess.run([accuracy, cross_entropy],
                                               feed_dict={x_in: test_data, t: test_label, p_keep: 1})
                t2 = time.time()
                end_time = int(round(t2 * 1000))
                print('train acc,loss:', acc, loss, test_acc, test_loss, "time consume::", end_time - start_time)


if __name__ == '__main__':
    tf.app.run()
