Page({
  data: {
    issueType: '',
    issueDesc: ''
  },

  submitRepair() {
    if (!this.data.issueType) {
      return wx.showToast({ title: '请输入故障类型', icon: 'none' });
    }
    
    wx.showLoading({ title: '提交中...' });
    
    setTimeout(() => {
      wx.hideLoading();
      wx.showToast({ title: '报修成功', icon: 'success' });
      
      let orders = wx.getStorageSync('om_orders') || [];
      const now = new Date();
      
      // ✨ 核心修改：生成精确到秒的时间字符串，拼凑为工单号
      const year = now.getFullYear();
      const month = String(now.getMonth() + 1).padStart(2, '0');
      const day = String(now.getDate()).padStart(2, '0');
      const hour = String(now.getHours()).padStart(2, '0');
      const minute = String(now.getMinutes()).padStart(2, '0');
      const second = String(now.getSeconds()).padStart(2, '0');
      const orderNo = `REP${year}${month}${day}${hour}${minute}${second}`;

      const newOrder = {
        id: Date.now(),
        orderNo: orderNo,
        type: this.data.issueType,
        desc: this.data.issueDesc,
        time: now.toLocaleString(),
        status: 0 // 初始状态为 0 (已接单)
      };
      
      orders.unshift(newOrder); 
      wx.setStorageSync('om_orders', orders);

      this.setData({ issueType: '', issueDesc: '' });
      wx.navigateTo({ url: '/pages/om_list/om_list' });
      
    }, 600);
  },

  goToOrderList() {
    wx.navigateTo({ url: '/pages/om_list/om_list' });
  }
});