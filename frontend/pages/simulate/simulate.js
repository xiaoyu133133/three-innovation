Page({
  data: {
    hours: [],
    targetTime: '',
    buyCount: '',
    simulationResult: null,
    showDialog: false // 控制模拟结果弹窗的显示
  },

  onLoad() {
    const hours = [];
    for (let i = 0; i < 24; i++) {
      hours.push(i.toString().padStart(2, '0') + ':00');
    }
    const currentHour = new Date().getHours().toString().padStart(2, '0') + ':00';
    this.setData({ hours, targetTime: currentHour });
  },

  onTimeChange(e) {
    const selectedIndex = e.detail.value;
    this.setData({ targetTime: this.data.hours[selectedIndex] });
  },

  // 1. 点击计算，弹出结果框
  startSimulate() {
    if (!this.data.buyCount) {
      wx.showToast({ title: '请输入购电量', icon: 'none' });
      return;
    }

    wx.showLoading({ title: '智能定价中...' });

    wx.request({
      url: 'http://127.0.0.1:8000/api/simulate',
      method: 'POST',
      data: {
        buy_count: parseFloat(this.data.buyCount),
        target_time: this.data.targetTime
      },
      success: (res) => {
        if (res.data.status === 'success') {
          this.setData({
            simulationResult: res.data,
            showDialog: true // 数据拿到了，打开弹窗
          });
        } else {
          wx.showToast({ title: res.data.message || '模拟失败', icon: 'none' });
        }
      },
      complete: () => wx.hideLoading()
    });
  },

  // 用户点击取消
  closeDialog() {
    this.setData({ showDialog: false });
  },

  // 2. 弹窗内点击“购买”，提交交易并弹窗提示成功
  confirmTrade() {
    if (!this.data.simulationResult) return;

    wx.showLoading({ title: '处理中...' });

    const tradeData = {
      user_name: "哈班岔村村民",
      buy_count: parseFloat(this.data.buyCount),
      total_price: this.data.simulationResult.total_cost
    };

    wx.request({
      url: 'http://127.0.0.1:8000/api/trade',
      method: 'POST',
      data: tradeData,
      success: (res) => {
        if (res.data.status === 'success') {
          // 清空输入并关闭之前的弹窗
          this.setData({
            showDialog: false,
            buyCount: '',
            simulationResult: null
          });
          
          // 采用原生弹窗展示订单已提交
          wx.showModal({
            title: '交易成功',
            content: '订单已提交，您可以前往个人中心查看详情。',
            showCancel: false,
            confirmText: '我知道了'
          });
        }
      },
      complete: () => wx.hideLoading()
    });
  }
});