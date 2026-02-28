Page({
  data: {
    issueType: '',
    issueDesc: '',
    hasOrder: false, // 是否有工单
    activeStep: 0,
    steps: [
      { text: '已接单', desc: '运维工程师 王师傅 已接单，正赶往现场' },
      { text: '维修中', desc: '工程师正在排查/处理问题' },
      { text: '已完成', desc: '设备已恢复正常运行' }
    ]
  },

  submitRepair() {
    if (!this.data.issueType) {
      return wx.showToast({ title: '请输入故障类型', icon: 'none' });
    }
    wx.showLoading({ title: '提交中...' });
    setTimeout(() => {
      wx.hideLoading();
      wx.showToast({ title: '报修成功', icon: 'success' });
      // 生成工单并重置进度
      this.setData({ hasOrder: true, activeStep: 0 });
    }, 600);
  },

  advanceRepairStep() {
    if (this.data.activeStep < 2) {
      wx.vibrateShort();
      this.setData({ activeStep: this.data.activeStep + 1 });
      if (this.data.activeStep === 2) {
        wx.showToast({ title: '维修完成！', icon: 'success' });
      }
    }
  }
});