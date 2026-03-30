Page({
  data: {
    avatarUrl: '',
    nickName: ''
  },
  
  onShow() {
    this.setData({
      avatarUrl: wx.getStorageSync('user_avatar') || '',
      nickName: String(wx.getStorageSync('user_nickname') || '')
    });
  },

  // 获取微信原生头像并保存
  onChooseAvatar(e) {
    const url = e.detail.avatarUrl;
    this.setData({ avatarUrl: url });
    wx.setStorageSync('user_avatar', url);
  },

  // 纯文本形式抓取昵称（兼容微信原生输入和特殊符号 '.'）
  onInputNickname(e) {
    const name = String(e.detail.value);
    this.setData({ nickName: name });
    wx.setStorageSync('user_nickname', name);
  },

  // 退出登录，清空缓存并返回
  doLogout() {
    wx.showModal({
      title: '确认退出',
      content: '退出登录后将无法查看专属数据',
      confirmColor: '#ee0a24',
      success: (res) => {
        if (res.confirm) {
          wx.clearStorageSync(); // 秒清所有缓存
          wx.showToast({ title: '已退出', icon: 'success' });
          setTimeout(() => { wx.navigateBack(); }, 800); // 丝滑退回主页
        }
      }
    });
  }
});