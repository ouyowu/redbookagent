const cloud = require('wx-server-sdk');

cloud.init({ env: cloud.DYNAMIC_CURRENT_ENV });
const db = cloud.database();

exports.main = async (event, context) => {
  const wxContext = cloud.getWXContext();
  const { OPENID, APPID, UNIONID } = wxContext;

  try {
    const usersCollection = db.collection('users');
    const existing = await usersCollection.where({ openid: OPENID }).get();

    let user;
    if (existing.data.length === 0) {
      // 新用户注册
      const newUser = {
        openid: OPENID,
        appid: APPID,
        nickName: '',
        avatarUrl: '',
        gender: 0,
        city: '',
        district: '',
        level: 'P1',
        levelVerified: false,
        creditScore: 80,
        gamesPlayed: 0,
        bio: '',
        createdAt: db.serverDate(),
        updatedAt: db.serverDate(),
      };
      const result = await usersCollection.add({ data: newUser });
      user = { _id: result._id, ...newUser };
    } else {
      user = existing.data[0];
    }

    // 生成 token（正式版使用 JWT）
    const token = Buffer.from(`${OPENID}:${Date.now()}`).toString('base64');

    return { user, token, isNew: existing.data.length === 0 };
  } catch (err) {
    return { error: err.message };
  }
};
