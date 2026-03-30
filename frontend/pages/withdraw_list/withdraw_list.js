Page({
  data: {
    records: [],
    totalBalance: '0.00', 
    isEditMode: false,
    selectedIds: [],
    isAllSelected: false,
    stepsConfig: [
      { text: '待审核' },
      { text: '结算中' },
      { text: '已到账' }
    ]
  },

  onShow() {
    this.fetchRecords();
  },

  fetchRecords() {
    const myOpenId = wx.getStorageSync('user_openid');
    if (!myOpenId) {
      this.setData({ records: [], totalBalance: '0.00' });
      return wx.showToast({ title: '请先登录查看记录', icon: 'none' });
    }

    wx.showNavigationBarLoading();
    wx.request({
      url: 'https://466eb478.r7.cpolar.cn/api/withdraws',
      method: 'GET',
      header: { 'x-wx-openid': myOpenId }, // ✨ 核心：带上身份证查记录
      success: (res) => {
        if (res.data.error) return; // 拦截报错
        
        const data = res.data.data.map(item => ({ ...item, showSteps: false }));
        this.setData({ 
          records: data,
          isEditMode: data.length === 0 ? false : this.data.isEditMode 
        });
        
        this.calculateTotal();
        this.checkAllSelected();
      },
      complete: () => wx.hideNavigationBarLoading()
    });
  },

  calculateTotal() {
    const total = this.data.records
      .filter(record => record.status === 2)
      .reduce((sum, record) => sum + record.amount, 0);
      
    this.setData({ totalBalance: total.toFixed(2) });
  },

  // ✨ 核心修改：统一处理卡片的点击事件
  onCardTap(e) {
    if (this.data.isEditMode) {
      // 1. 如果在长按删除模式下：点击卡片为【选中/取消选中】
      const id = e.currentTarget.dataset.id.toString();
      let ids = [...this.data.selectedIds];
      const index = ids.indexOf(id);
      if (index > -1) ids.splice(index, 1);
      else ids.push(id);
      this.setData({ selectedIds: ids });
      this.checkAllSelected();
    } else {
      // 2. 如果在普通模式下：点击卡片为【手风琴式展开/收起】
      const targetIndex = e.currentTarget.dataset.index;
      
      const newRecords = this.data.records.map((item, idx) => {
        return {
          ...item,
          showSteps: idx === targetIndex ? !item.showSteps : false
        };
      });

      this.setData({ records: newRecords });
    }
  },

  // 推进进度的交互保持不变
  // 推进进度的交互
  advanceStep(e) {
    if (this.data.isEditMode) return;
    
    const { index, id } = e.currentTarget.dataset;
    const record = this.data.records[index];

    if (record.status < 2) {
      wx.vibrateShort(); 
      const newStatus = record.status + 1;
      const statusKey = `records[${index}].status`;
      
      this.setData({ [statusKey]: newStatus }, () => {
        this.calculateTotal(); 
      });

      const myOpenId = wx.getStorageSync('user_openid');
      wx.request({
        url: `https://466eb478.r7.cpolar.cn/api/withdraws/${id}/advance`,
        method: 'PUT',
        header: { 'x-wx-openid': myOpenId } // ✨ 规范操作带上头部
      });
    }
  },

  // --- 多选删除等辅助逻辑 ---
  enterEditMode() {
    if (!this.data.isEditMode) {
      wx.vibrateShort();
      // 进入编辑模式时，强制收起所有已展开的进度条，保持界面干净
      const closedRecords = this.data.records.map(item => ({ ...item, showSteps: false }));
      this.setData({ isEditMode: true, selectedIds: [], isAllSelected: false, records: closedRecords });
    }
  },
  exitEditMode() { this.setData({ isEditMode: false, selectedIds: [], isAllSelected: false }); },
  onCheckboxChange(e) { this.setData({ selectedIds: e.detail }); this.checkAllSelected(); },
  
  checkAllSelected() {
    const all = this.data.records.length > 0 && this.data.selectedIds.length === this.data.records.length;
    this.setData({ isAllSelected: all });
  },
  selectAll() {
    if (this.data.isAllSelected) {
      this.setData({ selectedIds: [], isAllSelected: false });
    } else {
      const allIds = this.data.records.map(item => item.id.toString());
      this.setData({ selectedIds: allIds, isAllSelected: true });
    }
  },
  deleteSelected() {
    const { selectedIds } = this.data;
    if (selectedIds.length === 0) return;
    
    const myOpenId = wx.getStorageSync('user_openid');

    wx.showModal({
      title: '确认删除',
      content: `确定要删除这 ${selectedIds.length} 条记录吗？`,
      confirmColor: '#ee0a24',
      success: (res) => {
        if (res.confirm) {
          wx.showLoading({ title: '删除中...' });
          const deletePromises = selectedIds.map(id => {
            return new Promise((resolve) => {
              wx.request({ 
                url: `https://466eb478.r7.cpolar.cn/api/withdraws/${id}`, 
                method: 'DELETE', 
                header: { 'x-wx-openid': myOpenId }, // ✨ 规范操作带上头部
                success: resolve, 
                fail: resolve 
              });
            });
          });

          Promise.all(deletePromises).then(() => {
            wx.hideLoading();
            wx.showToast({ title: '已删除', icon: 'success' });
            this.setData({ selectedIds: [], isAllSelected: false });
            this.fetchRecords(); 
          });
        }
      }
    });
  }
});