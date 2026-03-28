Page({
  data: {
    isLoggedIn: false // ✨ 默认未登录状态
  },

  onLoad() {
    // ✨ 页面加载时检查是否有有效的登录 token
    const token = wx.getStorageSync('user_token');
    if (token) {
      this.setData({ isLoggedIn: true });
    }
  },

  // ✨ 核心逻辑：发起微信一键登录
  doLogin() {
    wx.showLoading({ title: '安全登录中...' });
    
    // 1. 获取微信临时登录凭证 code
    wx.login({
      success: (res) => {
        if (res.code) {
          // 2. 发送 code 到我们的后端
          wx.request({
            url: 'http://127.0.0.1:8000/api/login',
            method: 'POST',
            data: { code: res.code },
            success: (backendRes) => {
              wx.hideLoading();
              if (backendRes.data.status === 'success') {
                wx.showToast({ title: '登录成功', icon: 'success' });
                
                // 3. 存储后端下发的 token 和 openid 到本地缓存
                wx.setStorageSync('user_token', backendRes.data.data.token);
                wx.setStorageSync('user_openid', backendRes.data.data.openid);
                
                // 4. 更新界面为已登录状态
                this.setData({ isLoggedIn: true });
              } else {
                wx.showToast({ title: backendRes.data.message || '登录失败', icon: 'none' });
              }
            },
            fail: () => {
              wx.hideLoading();
              wx.showToast({ title: '网络请求失败，请检查后端', icon: 'none' });
            }
          });
        } else {
          wx.hideLoading();
          wx.showToast({ title: '获取微信鉴权失败', icon: 'none' });
        }
      }
    });
  },

  // ---- 下方是你原来保留的完美跳转逻辑 ----
  goToOrderList() { wx.navigateTo({ url: '/pages/order_list/order_list' }); },
  goToStationInfo() { wx.navigateTo({ url: '/pages/station_info/station_info' }); },
  goToSurplus() { wx.navigateTo({ url: '/pages/surplus/surplus' }); },
  goToCarbonPoints() { wx.navigateTo({ url: '/pages/carbon_points/carbon_points' }); },
  goToVillageSummary() { wx.navigateTo({ url: '/pages/village_summary/village_summary' }); },
  goToPolicies() { wx.navigateTo({ url: '/pages/policies/policies' }); },
  goToOMManage() { wx.navigateTo({ url: '/pages/om_manage/om_manage' }); }
});