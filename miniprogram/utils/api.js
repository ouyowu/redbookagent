// API 层 - 开发阶段使用 mock 数据，正式版切换 USE_MOCK = false
const mock = require('./mock');
const { CREDIT_RULES, INITIAL_CREDIT_SCORE } = require('./constants');

const USE_MOCK = true;

// 延迟模拟网络请求
const delay = (ms = 300) => new Promise(resolve => setTimeout(resolve, ms));

const api = {
  // ===== 用户相关 =====
  async login(code) {
    if (USE_MOCK) {
      await delay();
      return { user: mock.currentUser, token: 'mock_token_xxx' };
    }
    return wx.cloud.callFunction({ name: 'login', data: { code } });
  },

  async getUserInfo(userId) {
    if (USE_MOCK) {
      await delay();
      const user = mock.mockUsers.find(u => u._id === userId) || mock.currentUser;
      return user;
    }
    return wx.cloud.callFunction({ name: 'getUserInfo', data: { userId } });
  },

  async updateUserInfo(data) {
    if (USE_MOCK) {
      await delay();
      Object.assign(mock.currentUser, data);
      return { success: true };
    }
    return wx.cloud.callFunction({ name: 'updateUserInfo', data });
  },

  async getPlayers({ city, level, page = 1, pageSize = 20 } = {}) {
    if (USE_MOCK) {
      await delay();
      let users = [...mock.mockUsers];
      if (city) users = users.filter(u => u.city === city);
      if (level) users = users.filter(u => u.level === level);
      return { list: users, total: users.length };
    }
    return wx.cloud.callFunction({ name: 'getPlayers', data: { city, level, page, pageSize } });
  },

  // ===== 球局相关 =====
  async getGames({ city, district, status, level, page = 1, pageSize = 20 } = {}) {
    if (USE_MOCK) {
      await delay();
      let games = [...mock.mockGames];
      if (city) games = games.filter(g => g.city === city);
      if (district) games = games.filter(g => g.district === district);
      if (status) games = games.filter(g => g.status === status);
      return { list: games, total: games.length };
    }
    return wx.cloud.callFunction({ name: 'getGames', data: { city, district, status, level, page, pageSize } });
  },

  async getGameDetail(gameId) {
    if (USE_MOCK) {
      await delay();
      const game = mock.mockGames.find(g => g._id === gameId);
      return game || null;
    }
    return wx.cloud.callFunction({ name: 'getGameDetail', data: { gameId } });
  },

  async createGame(data) {
    if (USE_MOCK) {
      await delay();
      const newGame = {
        _id: `game_${Date.now()}`,
        creatorId: mock.currentUser._id,
        creator: mock.currentUser,
        currentPlayers: 1,
        participants: [mock.currentUser],
        status: 'OPEN',
        createdAt: new Date().toISOString().split('T')[0],
        ...data,
      };
      mock.mockGames.unshift(newGame);
      return { gameId: newGame._id };
    }
    return wx.cloud.callFunction({ name: 'createGame', data });
  },

  async joinGame(gameId) {
    if (USE_MOCK) {
      await delay();
      const game = mock.mockGames.find(g => g._id === gameId);
      if (!game) return { success: false, message: '球局不存在' };
      if (game.currentPlayers >= game.maxPlayers) return { success: false, message: '球局已满员' };
      const alreadyJoined = game.participants.some(p => p._id === mock.currentUser._id);
      if (alreadyJoined) return { success: false, message: '您已申请过该球局' };
      game.currentPlayers += 1;
      game.participants.push(mock.currentUser);
      if (game.currentPlayers >= game.maxPlayers) game.status = 'FULL';
      return { success: true, status: 'APPROVED' };
    }
    return wx.cloud.callFunction({ name: 'joinGame', data: { gameId } });
  },

  async cancelJoinGame(gameId) {
    if (USE_MOCK) {
      await delay();
      const game = mock.mockGames.find(g => g._id === gameId);
      if (!game) return { success: false };
      game.participants = game.participants.filter(p => p._id !== mock.currentUser._id);
      game.currentPlayers = Math.max(0, game.currentPlayers - 1);
      if (game.status === 'FULL') game.status = 'OPEN';
      return { success: true };
    }
    return wx.cloud.callFunction({ name: 'cancelJoinGame', data: { gameId } });
  },

  async getMyGames(type = 'joined') {
    if (USE_MOCK) {
      await delay();
      const userId = mock.currentUser._id;
      let games;
      if (type === 'created') {
        games = mock.mockGames.filter(g => g.creatorId === userId);
      } else {
        games = mock.mockGames.filter(g => g.participants.some(p => p._id === userId));
      }
      return { list: games };
    }
    return wx.cloud.callFunction({ name: 'getMyGames', data: { type } });
  },

  // ===== 视频认证 =====
  async uploadSkillVideo(data) {
    if (USE_MOCK) {
      await delay(1000);
      return {
        success: true,
        videoId: `video_${Date.now()}`,
        status: 'pending',
        message: '视频已提交，审核通常在24小时内完成',
      };
    }
    return wx.cloud.callFunction({ name: 'uploadVideo', data });
  },

  // ===== 评价相关 =====
  hasReviewed(gameId, revieweeId) {
    if (!USE_MOCK) return false;
    const key = `${mock.currentUser._id}_${gameId}_${revieweeId}`;
    return !!mock.submittedReviews[key];
  },

  async submitReview(data) {
    if (USE_MOCK) {
      await delay();
      const key = `${mock.currentUser._id}_${data.gameId}_${data.revieweeId}`;
      if (mock.submittedReviews[key]) return { success: false, message: '已评价过该球友' };

      mock.submittedReviews[key] = true;
      const newReview = {
        _id: `review_${Date.now()}`,
        reviewerId: mock.currentUser._id,
        reviewer: mock.currentUser,
        createdAt: new Date().toISOString().split('T')[0],
        ...data,
      };
      mock.mockReviews.push(newReview);

      // 更新被评价者信用分
      const reviewee = mock.mockUsers.find(u => u._id === data.revieweeId);
      if (reviewee) {
        let change = 0;
        if (data.isPunctual) change += CREDIT_RULES.PUNCTUAL.change;
        if (data.rating >= 4) change += CREDIT_RULES.GOOD_REVIEW.change;
        else if (data.rating <= 2) change += CREDIT_RULES.BAD_REVIEW.change;
        reviewee.creditScore = Math.max(0, Math.min(100, reviewee.creditScore + change));
      }
      return { success: true };
    }
    return wx.cloud.callFunction({ name: 'submitReview', data });
  },

  async getUserReviews(userId) {
    if (USE_MOCK) {
      await delay();
      return mock.mockReviews.filter(r => r.revieweeId === userId);
    }
    return wx.cloud.callFunction({ name: 'getUserReviews', data: { userId } });
  },

  // ===== 信用日志 =====
  async getCreditLogs(userId) {
    if (USE_MOCK) {
      await delay();
      return mock.mockCreditLogs.filter(l => l.userId === userId);
    }
    return wx.cloud.callFunction({ name: 'getCreditLogs', data: { userId } });
  },

  // ===== 消息 =====
  async getMessages() {
    if (USE_MOCK) {
      await delay();
      return mock.mockMessages;
    }
    return wx.cloud.callFunction({ name: 'getMessages' });
  },

  async markMessageRead(msgId) {
    if (USE_MOCK) {
      await delay();
      const msg = mock.mockMessages.find(m => m._id === msgId);
      if (msg) msg.isRead = true;
      return { success: true };
    }
    return wx.cloud.callFunction({ name: 'markMessageRead', data: { msgId } });
  },
};

module.exports = api;
