import cv2
import numpy as np
from model.inference import gaussian_blur, get_max_preds, taylor
from model.unet import get_pose_net
import torch


def convert_img(img):
    """
    pytorch 的训练方式是通道优先
    将 HWC 转为 CWH
    """

    # H  W  C ---> C  H  W ----> C W H
    img = torch.from_numpy(img).float()
    if len(img.shape) == 2:
        img = img.unsqueeze(0)
    elif len(img.shape) == 3:
        img = img.transpose(0, 2).transpose(1, 2)

    return img


# -----------定义图片预处理--------------------------
def load_and_convert_image(ori_img, input_imag_size=(256, 512), convert=True):
    img = cv2.resize(ori_img, input_imag_size)

    ori_img = np.array(ori_img)
    ori_img = torch.from_numpy(ori_img).float()
    img = np.array(img)
    if convert:
        img = convert_img(img)
    img = img - img.mean()
    img /= img.std()
    img /= img.max()

    return img.unsqueeze(dim=0), ori_img.unsqueeze(dim=0)  # chw: channel height width


def get_pred(hm):
    coords, maxvals = get_max_preds(hm)

    # post-processing
    hm = gaussian_blur(hm, 11)
    hm = np.maximum(hm, 1e-10)
    hm = np.log(hm)
    for n in range(coords.shape[0]):
        for p in range(coords.shape[1]):
            coords[n, p] = taylor(hm[n][p], coords[n][p])

    preds = coords.copy()
    return preds, maxvals


# --------------------模型预测-----------------------------
# 使用模型对指定图片文件路径完成图像分类，返回值为预测的种类名称
def predict_image(model, input_map, ori_img):
    output = model(input_map)
    out_shape = output.shape
    pred, _ = get_pred(output.detach().numpy())

    ori_w = ori_img.shape[2]
    ori_h = ori_img.shape[1]
    out_w = out_shape[3]
    out_h = out_shape[2]

    batch_size = output.shape[0]
    norm = np.array([ori_w / out_w, ori_h / out_h]).reshape(batch_size, 1, 2)
    pred = pred * norm
    return pred


def load_model(model_path='static/model_best.pth'):
    model = get_pose_net(37)
    model.load_state_dict(torch.load(model_path, map_location='cpu'), strict=False)
    return model


model = load_model()


def auto_get_points(img):
    input_map, ori_img = load_and_convert_image(img)

    # 得到关键点
    result = predict_image(model, input_map, ori_img)

    return result[0]
