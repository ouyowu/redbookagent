const cloud = require('wx-server-sdk');

cloud.init({ env: cloud.DYNAMIC_CURRENT_ENV });
const db = cloud.database();
const _ = db.command;

exports.main = async (event, context) => {
  const wxContext = cloud.getWXContext();
  const { OPENID } = wxContext;

  try {
    const userResult = await db.collection('users').where({ openid: OPENID }).get();
    if (!userResult.data.length) return { error: '用户不存在' };
    const user = userResult.data[0];

    const gameResult = await db.collection('games').doc(event.gameId).get();
    const game = gameResult.data;

    if (game.status === 'FULL' || game.currentPlayers >= game.maxPlayers) {
      return { success: false, message: '球局已满员' };
    }

    if (game.status !== 'OPEN') {
      return { success: false, message: '球局不在招募中' };
    }

    // 检查是否已申请
    const existing = await db.collection('game_participants').where({
      gameId: event.gameId,
      userId: user._id,
    }).get();

    if (existing.data.length > 0) {
      return { success: false, message: '您已申请过该球局' };
    }

    // 判断水平是否符合
    const levels = ['P1', 'P2', 'P3', 'P4', 'P5', 'P6'];
    const userLevelIdx = levels.indexOf(user.level);
    const minLevelIdx = levels.indexOf(game.minLevel);
    const maxLevelIdx = levels.indexOf(game.maxLevel);

    if (userLevelIdx < minLevelIdx || userLevelIdx > maxLevelIdx) {
      return { success: false, message: `水平要求 ${game.minLevel}~${game.maxLevel}，您当前为 ${user.level}` };
    }

    // 加入球局
    await db.collection('game_participants').add({
      data: {
        gameId: event.gameId,
        userId: user._id,
        status: 'APPROVED',
        joinedAt: db.serverDate(),
      },
    });

    const newCount = game.currentPlayers + 1;
    const newStatus = newCount >= game.maxPlayers ? 'FULL' : 'OPEN';

    await db.collection('games').doc(event.gameId).update({
      data: {
        currentPlayers: _.inc(1),
        status: newStatus,
      },
    });

    return { success: true, status: 'APPROVED' };
  } catch (err) {
    return { error: err.message };
  }
};
