const app = getApp();
const { getLevelInfo, getCreditLevel, showToast } = require('../../utils/util');
const { PICKLEBALL_LEVELS } = require('../../utils/constants');

const CARD_GRADIENTS = [
  'linear-gradient(135deg, #667EEA 0%, #764BA2 100%)',
  'linear-gradient(135deg, #F093FB 0%, #F5576C 100%)',
  'linear-gradient(135deg, #43E97B 0%, #38A169 100%)',
  'linear-gradient(135deg, #FA709A 0%, #FEE140 100%)',
  'linear-gradient(135deg, #4FACFE 0%, #00F2FE 100%)',
  'linear-gradient(135deg, #F7971E 0%, #FFD200 100%)',
];

const BADGES = [
  { id: 'first_game', icon: '🏸', name: '初次出击', bg: '#E6FAF2', minGames: 1 },
  { id: 'ten_games', icon: '🔥', name: '球场常客', bg: '#FFF3E0', minGames: 10 },
  { id: 'thirty_games', icon: '⚡', name: '球场老将', bg: '#EDF2FF', minGames: 30 },
  { id: 'credit_90', icon: '⭐', name: '信誉达人', bg: '#FFFBE6', minCredit: 90 },
  { id: 'verified', icon: '🎖', name: '认证球员', bg: '#F3EDFF', needVerified: true },
  { id: 'level_p4', icon: '🏆', name: 'P4以上', bg: '#FFF0EE', minLevelIdx: 3 },
  { id: 'level_p5', icon: '👑', name: 'P5精英', bg: '#E6FAF2', minLevelIdx: 4 },
  { id: 'level_p6', icon: '💎', name: 'P6大神', bg: '#EDF2FF', minLevelIdx: 5 },
];

Page({
  data: {
    userInfo: null,
    levelInfo: null,
    creditLevel: null,
    cardGradient: '',
    allLevels: [],
    badges: [],
  },

  onShow() {
    const userInfo = app.globalData.userInfo;
    if (!userInfo) {
      wx.navigateBack();
      return;
    }
    const levelInfo = getLevelInfo(userInfo.level);
    const creditLevel = getCreditLevel(userInfo.creditScore);
    const levelKeys = Object.keys(PICKLEBALL_LEVELS);
    const userLevelIdx = levelKeys.indexOf(userInfo.level);

    const allLevels = levelKeys.map((key, idx) => ({
      key,
      ...PICKLEBALL_LEVELS[key],
      reached: idx <= userLevelIdx,
    }));

    const badges = BADGES.map(b => {
      let earned = false;
      if (b.minGames !== undefined) earned = userInfo.gamesPlayed >= b.minGames;
      else if (b.minCredit !== undefined) earned = userInfo.creditScore >= b.minCredit;
      else if (b.needVerified) earned = !!userInfo.levelVerified;
      else if (b.minLevelIdx !== undefined) earned = userLevelIdx >= b.minLevelIdx;
      return { ...b, earned };
    });

    const hash = userInfo._id ? userInfo._id.charCodeAt(userInfo._id.length - 1) % CARD_GRADIENTS.length : 0;

    this.setData({
      userInfo,
      levelInfo,
      creditLevel,
      cardGradient: CARD_GRADIENTS[hash],
      allLevels,
      badges,
    });
  },

  onBack() {
    wx.navigateBack();
  },

  onShare() {
    showToast('分享功能即将上线');
  },

  onUploadVideo() {
    wx.navigateTo({ url: '/pages/video-upload/video-upload' });
  },
});
