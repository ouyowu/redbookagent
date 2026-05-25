const app = getApp();
const api = require('../../utils/api');
const { showToast } = require('../../utils/util');

Page({
  data: {
    form: {
      nickName: '',
      avatarUrl: '',
      gender: 0,
      city: '',
      district: '',
      bio: '',
    },
    genderOptions: ['保密', '男', '女'],
    submitting: false,
    isNew: false,
  },

  onLoad(options) {
    const isNew = options.isNew === 'true';
    const userInfo = app.globalData.userInfo || {};
    this.setData({
      isNew,
      form: {
        nickName: userInfo.nickName || '',
        avatarUrl: userInfo.avatarUrl || '',
        gender: userInfo.gender || 0,
        city: userInfo.city || '',
        district: userInfo.district || '',
        bio: userInfo.bio || '',
      },
    });
  },

  onChooseAvatar(e) {
    const { avatarUrl } = e.detail;
    this.setData({ 'form.avatarUrl': avatarUrl });
  },

  onInput(e) {
    const { field } = e.currentTarget.dataset;
    this.setData({ [`form.${field}`]: e.detail.value });
  },

  onGenderChange(e) {
    this.setData({ 'form.gender': Number(e.detail.value) });
  },

  validate() {
    if (!this.data.form.nickName.trim()) {
      showToast('请填写昵称');
      return false;
    }
    return true;
  },

  async onSubmit() {
    if (!this.validate() || this.data.submitting) return;
    this.setData({ submitting: true });

    try {
      await api.updateUserInfo(this.data.form);
      app.updateUserInfo(this.data.form);
      showToast('保存成功', 'success');
      setTimeout(() => {
        if (this.data.isNew) {
          wx.switchTab({ url: '/pages/index/index' });
        } else {
          wx.navigateBack();
        }
      }, 1000);
    } catch (err) {
      showToast('保存失败，请重试');
    } finally {
      this.setData({ submitting: false });
    }
  },
});
