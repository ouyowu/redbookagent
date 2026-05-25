const cloud = require('wx-server-sdk');

cloud.init({ env: cloud.DYNAMIC_CURRENT_ENV });
const db = cloud.database();

exports.main = async (event, context) => {
  const wxContext = cloud.getWXContext();
  const { OPENID } = wxContext;

  try {
    const userResult = await db.collection('users').where({ openid: OPENID }).get();
    if (!userResult.data.length) return { error: '用户不存在' };
    const user = userResult.data[0];

    const newGame = {
      creatorId: user._id,
      title: event.title,
      description: event.description || '',
      venue: event.venue,
      address: event.address || '',
      city: event.city || user.city,
      district: event.district || user.district,
      date: event.date,
      startTime: event.startTime,
      endTime: event.endTime,
      maxPlayers: event.maxPlayers || 4,
      currentPlayers: 1,
      minLevel: event.minLevel || 'P1',
      maxLevel: event.maxLevel || 'P6',
      fee: event.fee || 0,
      status: 'OPEN',
      createdAt: db.serverDate(),
    };

    const result = await db.collection('games').add({ data: newGame });

    // 自动将发起人加入
    await db.collection('game_participants').add({
      data: {
        gameId: result._id,
        userId: user._id,
        status: 'APPROVED',
        joinedAt: db.serverDate(),
      },
    });

    return { success: true, gameId: result._id };
  } catch (err) {
    return { error: err.message };
  }
};
