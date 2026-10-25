const app = getApp();
const api = require('../../utils/api');
const { showToast } = require('../../utils/util');

Page({
  data: {
    form: {
      title: '',
      venue: '',
      address: '',
      district: '',
      date: '',
      startTime: '',
      endTime: '',
      maxPlayers: 4,
      minLevel: 'P1',
      maxLevel: 'P6',
      fee: 0,
      description: '',
    },
    levelOptions: ['P1', 'P2', 'P3', 'P4', 'P5', 'P6'],
    playerOptions: [2, 4, 6, 8, 10, 12],
    submitting: false,
    minDate: new Date().toISOString().split('T')[0],
  },

  onLoad() {
    const today = new Date();
    today.setDate(today.getDate() + 1);
    this.setData({ 'form.date': today.toISOString().split('T')[0] });
  },

  onInput(e) {
    const { field } = e.currentTarget.dataset;
    this.setData({ [`form.${field}`]: e.detail.value });
  },

  onPickerChange(e) {
    const { field } = e.currentTarget.dataset;
    this.setData({ [`form.${field}`]: e.detail.value });
  },

  onMaxPlayersChange(e) {
    this.setData({ 'form.maxPlayers': this.data.playerOptions[e.detail.value] });
  },

  onMinLevelChange(e) {
    this.setData({ 'form.minLevel': this.data.levelOptions[e.detail.value] });
  },

  onMaxLevelChange(e) {
    this.setData({ 'form.maxLevel': this.data.levelOptions[e.detail.value] });
  },

  validate() {
    const { form } = this.data;
    if (!form.title.trim()) { showToast('请填写球局标题'); return false; }
    if (!form.venue.trim()) { showToast('请填写场地名称'); return false; }
    if (!form.date) { showToast('请选择日期'); return false; }
    if (!form.startTime) { showToast('请选择开始时间'); return false; }
    if (!form.endTime) { showToast('请选择结束时间'); return false; }
    return true;
  },

  async onSubmit() {
    if (!this.validate() || this.data.submitting) return;
    this.setData({ submitting: true });

    try {
      const result = await api.createGame({
        ...this.data.form,
        city: app.globalData.userInfo?.city || '上海',
        fee: Number(this.data.form.fee) || 0,
      });
      showToast('球局发布成功！', 'success');
      setTimeout(() => {
        wx.redirectTo({ url: `/pages/game-detail/game-detail?id=${result.gameId}` });
      }, 1200);
    } catch (err) {
      showToast('发布失败，请重试');
    } finally {
      this.setData({ submitting: false });
    }
  },
});
