Page({
  goToOrderList() { wx.navigateTo({ url: '/pages/order_list/order_list' }); },
  goToStationInfo() { wx.navigateTo({ url: '/pages/station_info/station_info' }); },
  // ✨ 新增跳转
  goToSurplus() { wx.navigateTo({ url: '/pages/surplus/surplus' }); }
});