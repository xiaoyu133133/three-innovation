Page({
  data: {
    isLoggedIn: false,
    avatarUrl: '',
    nickName: ''
  },

  // 使用 onShow 确保从个人信息页返回时，能瞬间刷新头像和昵称
  onShow() {
    const token = wx.getStorageSync('user_token');
    if (token) {
      this.setData({ 
        isLoggedIn: true,
        avatarUrl: wx.getStorageSync('user_avatar') || '',
        nickName: String(wx.getStorageSync('user_nickname') || '')
      });
    } else {
      this.setData({ isLoggedIn: false, avatarUrl: '', nickName: '' });
    }
  },

  // 极简静默登录，无任何弹窗
  doLogin() {
    wx.showLoading({ title: '安全登录中...' });
    
    wx.login({
      success: (res) => {
        if (res.code) {
          wx.request({
            url: 'http://127.0.0.1:8000/api/login',
            method: 'POST',
            data: { code: res.code },
            success: (backendRes) => {
              wx.hideLoading();
              if (backendRes.data.status === 'success') {
                wx.setStorageSync('user_token', backendRes.data.data.token);
                wx.setStorageSync('user_openid', backendRes.data.data.openid);
                this.setData({ isLoggedIn: true });
                
                // 登录成功后，如果发现没头像昵称，给个吐司引导去个人信息页
                if (!wx.getStorageSync('user_avatar') || !wx.getStorageSync('user_nickname')) {
                  wx.showToast({ title: '请点击上方区域完善信息', icon: 'none', duration: 3000 });
                } else {
                  wx.showToast({ title: '欢迎回来', icon: 'success' });
                }
              } else {
                wx.showToast({ title: backendRes.data.message, icon: 'none' });
              }
            },
            fail: () => { wx.hideLoading(); wx.showToast({ title: '网络异常', icon: 'none' }); }
          });
        }
      }
    });
  },

  // 跳转至独立的个人信息页
  goToProfile() { wx.navigateTo({ url: '/pages/profile/profile' }); },

  // --- 路由 ---
  goToOrderList() { wx.navigateTo({ url: '/pages/order_list/order_list' }); },
  goToStationInfo() { wx.navigateTo({ url: '/pages/station_info/station_info' }); },
  goToSurplus() { wx.navigateTo({ url: '/pages/surplus/surplus' }); },
  goToCarbonPoints() { wx.navigateTo({ url: '/pages/carbon_points/carbon_points' }); },
  goToVillageSummary() { wx.navigateTo({ url: '/pages/village_summary/village_summary' }); },
  goToPolicies() { wx.navigateTo({ url: '/pages/policies/policies' }); },
  goToOMManage() { wx.navigateTo({ url: '/pages/om_manage/om_manage' }); }
});