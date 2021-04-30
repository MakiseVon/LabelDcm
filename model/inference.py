from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
import cv2
import numpy as np


# 获得中心坐标作为关键点
def get_center_preds(batch_heatmaps, threshold=0.2):
    assert isinstance(batch_heatmaps, np.ndarray), 'batch_heatmaps should be numpy.ndarray'
    assert batch_heatmaps.ndim == 4, 'batch_images should be 4-ndim'

    batch_size = batch_heatmaps.shape[0]
    num_joints = batch_heatmaps.shape[1]
    pred_index = np.zeros((batch_size, num_joints, 2), dtype=np.float)
    for i in range(batch_size):
        for j in range(num_joints):
            hm = batch_heatmaps[i][j]
            hindex = (hm > threshold).nonzero()
            pred_index[i][j] = np.mean(hindex, axis=1)  # 横纵坐标

    return pred_index, 0


# 获取最大的响应的坐标
def get_max_preds(batch_heatmaps):
    """
    get predictions from score maps
    heatmaps: numpy.ndarray([batch_size, num_joints, height, width])
    """
    assert isinstance(batch_heatmaps, np.ndarray), 'batch_heatmaps should be numpy.ndarray'
    assert batch_heatmaps.ndim == 4, 'batch_images should be 4-ndim'

    batch_size = batch_heatmaps.shape[0]
    num_joints = batch_heatmaps.shape[1]
    width = batch_heatmaps.shape[3]
    heatmaps_reshaped = batch_heatmaps.reshape((batch_size, num_joints, -1))
    idx = np.argmax(heatmaps_reshaped, 2)
    maxvals = np.amax(heatmaps_reshaped, 2)

    maxvals = maxvals.reshape((batch_size, num_joints, 1))
    idx = idx.reshape((batch_size, num_joints, 1))

    preds = np.tile(idx, (1, 1, 2)).astype(np.float32)

    preds[:, :, 0] = (preds[:, :, 0]) % width  # 得到列数
    preds[:, :, 1] = np.floor((preds[:, :, 1]) / width)  # 得到行数

    pred_mask = np.tile(np.greater(maxvals, 0.0), (1, 1, 2))  # 只有最大值大于 0 才有效
    pred_mask = pred_mask.astype(np.float32)

    preds *= pred_mask

    return preds, maxvals


def taylor(hm, coord):
    heatmap_height = hm.shape[0]
    heatmap_width = hm.shape[1]
    px = int(coord[0])
    py = int(coord[1])
    if 1 < px < heatmap_width - 2 and 1 < py < heatmap_height - 2:
        dx = 0.5 * (hm[py][px + 1] - hm[py][px - 1])
        dy = 0.5 * (hm[py + 1][px] - hm[py - 1][px])
        dxx = 0.25 * (hm[py][px + 2] - 2 * hm[py][px] + hm[py][px - 2])
        dxy = 0.25 * (hm[py + 1][px + 1] - hm[py - 1][px + 1] - hm[py + 1][px - 1] + hm[py - 1][px - 1])
        dyy = 0.25 * (hm[py + 2 * 1][px] - 2 * hm[py][px] + hm[py - 2 * 1][px])
        derivative = np.matrix([[dx], [dy]])
        hessian = np.matrix([[dxx, dxy], [dxy, dyy]])
        if dxx * dyy - dxy ** 2 != 0:
            hessianinv = hessian.I
            offset = -hessianinv * derivative
            offset = np.squeeze(np.array(offset.T), axis=0)
            coord += offset
    return coord


def gaussian_blur(hm, kernel):
    border = (kernel - 1) // 2
    batch_size = hm.shape[0]
    num_joints = hm.shape[1]
    height = hm.shape[2]
    width = hm.shape[3]
    for i in range(batch_size):
        for j in range(num_joints):
            origin_max = np.max(hm[i, j])
            dr = np.zeros((height + 2 * border, width + 2 * border))
            dr[border: -border, border: -border] = hm[i, j].copy()
            dr = cv2.GaussianBlur(dr, (kernel, kernel), 0)
            hm[i, j] = dr[border: -border, border: -border].copy()
            hm[i, j] *= origin_max / np.max(hm[i, j])
    return hm


def get_final_preds(config, hm):
    coords, maxvals = get_max_preds(hm)

    # post-processing
    hm = gaussian_blur(hm, config.TEST.BLUR_KERNEL)
    hm = np.maximum(hm, 1e-10)
    hm = np.log(hm)
    for n in range(coords.shape[0]):
        for p in range(coords.shape[1]):
            coords[n, p] = taylor(hm[n][p], coords[n][p])

    preds = coords.copy()
    return preds, maxvals
