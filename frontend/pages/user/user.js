Page({
  goToOrderList() { wx.navigateTo({ url: '/pages/order_list/order_list' }); },
  goToStationInfo() { wx.navigateTo({ url: '/pages/station_info/station_info' }); },
  goToSurplus() { wx.navigateTo({ url: '/pages/surplus/surplus' }); },
  // ✨ 新增跳转
  // ... 前面的跳转保持不变
  goToCarbonPoints() { wx.navigateTo({ url: '/pages/carbon_points/carbon_points' }); },
  
  // ✨ 新增三个跳转
  goToVillageSummary() { wx.navigateTo({ url: '/pages/village_summary/village_summary' }); },
  goToPolicies() { wx.navigateTo({ url: '/pages/policies/policies' }); },
  goToOMManage() { wx.navigateTo({ url: '/pages/om_manage/om_manage' }); }
});