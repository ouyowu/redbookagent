const app = getApp();
const api = require('../../utils/api');
const { REVIEW_TAGS_POSITIVE, REVIEW_TAGS_NEGATIVE } = require('../../utils/constants');
const { showToast } = require('../../utils/util');

Page({
  data: {
    gameId: '',
    revieweeId: '',
    reviewee: null,
    rating: 0,
    selectedTags: [],
    comment: '',
    isPunctual: true,
    submitting: false,
    positiveTags: REVIEW_TAGS_POSITIVE,
    negativeTags: REVIEW_TAGS_NEGATIVE,
    showNegativeTags: false,
  },

  onLoad(options) {
    const { gameId, revieweeId } = options;
    this.setData({ gameId, revieweeId });
    this.loadReviewee(revieweeId);
  },

  async loadReviewee(userId) {
    try {
      const user = await api.getUserInfo(userId);
      this.setData({ reviewee: user });
    } catch (err) {
      showToast('加载失败');
    }
  },

  onRatingTap(e) {
    const rating = e.currentTarget.dataset.rating;
    const showNegativeTags = rating <= 2;
    this.setData({
      rating,
      showNegativeTags,
      selectedTags: [],
    });
  },

  onTagTap(e) {
    const tag = e.currentTarget.dataset.tag;
    const tags = [...this.data.selectedTags];
    const idx = tags.indexOf(tag);
    if (idx >= 0) {
      tags.splice(idx, 1);
    } else if (tags.length < 3) {
      tags.push(tag);
    } else {
      showToast('最多选3个标签');
      return;
    }
    this.setData({ selectedTags: tags });
  },

  onPunctualChange(e) {
    this.setData({ isPunctual: e.detail.value });
  },

  onCommentInput(e) {
    this.setData({ comment: e.detail.value });
  },

  async onSubmit() {
    if (this.data.rating === 0) {
      showToast('请先评分');
      return;
    }
    if (this.data.submitting) return;

    this.setData({ submitting: true });
    try {
      await api.submitReview({
        gameId: this.data.gameId,
        revieweeId: this.data.revieweeId,
        rating: this.data.rating,
        tags: this.data.selectedTags,
        comment: this.data.comment,
        isPunctual: this.data.isPunctual,
      });
      showToast('评价提交成功！', 'success');
      setTimeout(() => wx.navigateBack(), 1200);
    } catch (err) {
      showToast('提交失败，请重试');
    } finally {
      this.setData({ submitting: false });
    }
  },
});
