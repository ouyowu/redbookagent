const app = getApp();
const api = require('../../utils/api');
const { showToast } = require('../../utils/util');

Page({
  data: {
    videoPath: '',
    thumbPath: '',
    duration: 0,
    uploading: false,
    uploaded: false,
    levelOptions: [
      { key: 'P1', label: 'P1 新手', desc: '刚接触匹克球，学习基础动作' },
      { key: 'P2', label: 'P2 初级', desc: '掌握基本动作，能打简单对打' },
      { key: 'P3', label: 'P3 进阶', desc: '技术稳定，有一定战术意识' },
      { key: 'P4', label: 'P4 中高级', desc: '技术全面，具备较强比赛能力' },
      { key: 'P5', label: 'P5 高水平业余', desc: '技术出色，参加高水平比赛' },
      { key: 'P6', label: 'P6 竞技型', desc: '接近专业水平，参加竞技赛事' },
    ],
    selfRatedLevel: '',
    tips: [
      '时长 10~15 秒，展示您的实际球技',
      '视频清晰，能看清动作和球路',
      '建议拍摄双打或单打对练的自然状态',
      '审核团队会在 24 小时内完成评级',
    ],
  },

  onChooseVideo() {
    // 使用 chooseVideo（兼容性更好）
    wx.chooseVideo({
      sourceType: ['album', 'camera'],
      maxDuration: 20,
      camera: 'back',
      success: (res) => {
        if (res.duration > 20) {
          showToast('视频时长不能超过20秒');
          return;
        }
        this.setData({
          videoPath: res.tempFilePath,
          thumbPath: res.thumbTempFilePath || '',
          duration: Math.round(res.duration) || 10,
        });
      },
      fail: (err) => {
        if (err.errMsg && err.errMsg.indexOf('cancel') === -1) {
          showToast('选择视频失败，请重试');
        }
      },
    });
  },

  onGoBack() {
    wx.navigateBack();
  },

  onLevelSelect(e) {
    this.setData({ selfRatedLevel: e.currentTarget.dataset.level });
  },

  async onUpload() {
    if (!this.data.videoPath) {
      showToast('请先选择视频');
      return;
    }
    if (!this.data.selfRatedLevel) {
      showToast('请先选择您的自评等级');
      return;
    }
    if (this.data.uploading) return;

    this.setData({ uploading: true });
    try {
      // 正式版：先上传视频到云存储，再提交 URL
      const result = await api.uploadSkillVideo({
        videoPath: this.data.videoPath,
        selfRatedLevel: this.data.selfRatedLevel,
        duration: this.data.duration,
      });

      if (result.success) {
        this.setData({ uploaded: true });
        showToast('视频提交成功！', 'success');
      } else {
        showToast('上传失败，请重试');
      }
    } catch (err) {
      showToast('上传失败，请重试');
    } finally {
      this.setData({ uploading: false });
    }
  },
});
