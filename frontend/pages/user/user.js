Page({
  goToOrderList() { wx.navigateTo({ url: '/pages/order_list/order_list' }); },
  goToStationInfo() { wx.navigateTo({ url: '/pages/station_info/station_info' }); },
  goToSurplus() { wx.navigateTo({ url: '/pages/surplus/surplus' }); },
  // ✨ 新增跳转
  goToCarbonPoints() { wx.navigateTo({ url: '/pages/carbon_points/carbon_points' }); }
});