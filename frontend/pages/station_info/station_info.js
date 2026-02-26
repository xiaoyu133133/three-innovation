Page({
  data: {
    stationId: 'gs2026001',
    capacity: 500,
    gridTime: '2025-10-01',
    address: '甘肃省兰州市榆中县哈班岔村',
    team: '微电先锋——乡村光伏服务团队',
    
    score: 0,
    statusText: '检测中...',
    statusColor: '#999'
  },

  onShow() {
    this.updateStatusFromScore();
  },

  onDateChange(e) {
    this.setData({
      gridTime: e.detail.value
    });
  },

  updateStatusFromScore() {
    const score = wx.getStorageSync('currentEffScore') || 85;
    
    let statusText = '';
    let statusColor = '';

    // ✨ 核心修改：与主界面保持完全一致的 4 档评判规则与颜色
    if (score >= 90) {
      statusText = '优秀 (正常)';
      statusColor = '#07c160'; // 绿色
    } else if (score >= 80) {
      statusText = '良好';
      statusColor = '#1989fa'; // 蓝色
    } else if (score >= 70) {
      statusText = '一般';
      statusColor = '#ff976a'; // 橙色
    } else {
      statusText = '异常';
      statusColor = '#ee0a24'; // 红色
    }

    this.setData({
      score: score,
      statusText: statusText,
      statusColor: statusColor
    });
  }
});