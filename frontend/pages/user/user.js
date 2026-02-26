Page({
  goToOrderList() {
    wx.navigateTo({ url: '/pages/order_list/order_list' });
  },
  
  // ✨ 新增跳转逻辑
  goToStationInfo() {
    wx.navigateTo({ url: '/pages/station_info/station_info' });
  }
});