const cloud = require('wx-server-sdk');

cloud.init({ env: cloud.DYNAMIC_CURRENT_ENV });
const db = cloud.database();
const _ = db.command;

const CREDIT_RULES = {
  PUNCTUAL: 2,
  GOOD_REVIEW: 2,
  BAD_REVIEW: -3,
};

exports.main = async (event, context) => {
  const wxContext = cloud.getWXContext();
  const { OPENID } = wxContext;

  try {
    const reviewerResult = await db.collection('users').where({ openid: OPENID }).get();
    if (!reviewerResult.data.length) return { error: '用户不存在' };
    const reviewer = reviewerResult.data[0];

    // 防止重复评价
    const existing = await db.collection('reviews').where({
      gameId: event.gameId,
      reviewerId: reviewer._id,
      revieweeId: event.revieweeId,
    }).get();

    if (existing.data.length > 0) return { error: '已评价过该球友' };

    // 写入评价
    await db.collection('reviews').add({
      data: {
        gameId: event.gameId,
        reviewerId: reviewer._id,
        revieweeId: event.revieweeId,
        rating: event.rating,
        tags: event.tags || [],
        comment: event.comment || '',
        isPunctual: event.isPunctual,
        createdAt: db.serverDate(),
      },
    });

    // 计算信用分变化
    let creditChange = 0;
    if (event.isPunctual) creditChange += CREDIT_RULES.PUNCTUAL;
    if (event.rating >= 4) creditChange += CREDIT_RULES.GOOD_REVIEW;
    else if (event.rating <= 2) creditChange += CREDIT_RULES.BAD_REVIEW;

    if (creditChange !== 0) {
      // 更新信用分（clamp 0~100）
      const revieweeResult = await db.collection('users').doc(event.revieweeId).get();
      const currentScore = revieweeResult.data.creditScore;
      const newScore = Math.max(0, Math.min(100, currentScore + creditChange));

      await db.collection('users').doc(event.revieweeId).update({
        data: { creditScore: newScore, updatedAt: db.serverDate() },
      });

      // 写入信用日志
      const reason = event.rating >= 4 ? '获得好评' : event.rating <= 2 ? '获得差评' : '收到评价';
      await db.collection('credit_logs').add({
        data: {
          userId: event.revieweeId,
          change: creditChange,
          reason,
          gameId: event.gameId,
          newScore,
          createdAt: db.serverDate(),
        },
      });
    }

    return { success: true };
  } catch (err) {
    return { error: err.message };
  }
};
