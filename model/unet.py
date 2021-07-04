import torch
import torch.nn as nn
import warnings


warnings.filterwarnings("ignore", category=UserWarning)


def double_conv(in_channels, out_channels):
    return nn.Sequential(
        nn.Conv2d(in_channels, out_channels, 3, padding=1),
        nn.InstanceNorm2d(out_channels),
        nn.LeakyReLU(inplace=True),
        nn.Conv2d(out_channels, out_channels, 3, padding=1),
        nn.InstanceNorm2d(out_channels),
        nn.LeakyReLU(inplace=True)
    )


class UNet(nn.Module):
    def __init__(self, num_joint):
        super(UNet, self).__init__()
        ln = [32, 64, 128, 256]
        self.dconv_down1 = double_conv(3, ln[0])
        self.dconv_down2 = double_conv(ln[0], ln[1])
        self.dconv_down3 = double_conv(ln[1], ln[2])
        self.dconv_down4 = double_conv(ln[2], ln[3])
        self.maxpool = nn.MaxPool2d(2)
        self.upsample = nn.Upsample(scale_factor=2, mode='bilinear', align_corners=True)

        self.dconv_up3 = double_conv(ln[2] + ln[3], ln[2])
        self.dconv_up2 = double_conv(ln[1] + ln[2], ln[1])
        self.dconv_up1 = double_conv(ln[1] + ln[0], ln[0])

        self.conv_last = nn.Conv2d(ln[0], num_joint, 1)

    def get_feature_map(self, x):
        heatmap = []
        conv1 = self.dconv_down1(x)

        x = self.maxpool(conv1)
        conv2 = self.dconv_down2(x)

        x = self.maxpool(conv2)
        conv3 = self.dconv_down3(x)

        x = self.maxpool(conv3)
        x = self.dconv_down4(x)
        heatmap.append(x)

        x = self.upsample(x)
        x = torch.cat([x, conv3], dim=1)
        x = self.dconv_up3(x)
        heatmap.append(x)

        x = self.upsample(x)
        x = torch.cat([x, conv2], dim=1)
        x = self.dconv_up2(x)
        heatmap.append(x)

        return heatmap

    def forward(self, x):
        # local
        conv1 = self.dconv_down1(x)

        x = self.maxpool(conv1)
        conv2 = self.dconv_down2(x)

        x = self.maxpool(conv2)
        conv3 = self.dconv_down3(x)

        x = self.maxpool(conv3)
        x = self.dconv_down4(x)

        x = self.upsample(x)
        x = torch.cat([x, conv3], dim=1)
        x = self.dconv_up3(x)
        x = self.upsample(x)
        x = torch.cat([x, conv2], dim=1)
        x = self.dconv_up2(x)
        x = self.upsample(x)
        x = torch.cat([x, conv1], dim=1)
        x = self.dconv_up1(x)
        lout = self.conv_last(x)
        return lout


def get_pose_net(num_joint=37):
    model = UNet(num_joint)
    return model
