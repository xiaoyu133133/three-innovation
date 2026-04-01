Page({
  data: {
    orders: [],
    isEditMode: false,   // 是否处于长按编辑模式
    selectedIds: [],     // 已选中的订单 ID 数组
    isAllSelected: false // 是否全选
  },

  onShow() {
    this.fetchOrders();
  },

  fetchOrders() {
    wx.showNavigationBarLoading();
    wx.request({
      url: 'https://bd8d882.r9.vip.cpolar.cn/api/orders',
      method: 'GET',
      success: (res) => {
        this.setData({ 
          orders: res.data.data,
          // 如果删光了，自动退出编辑模式
          isEditMode: res.data.data.length === 0 ? false : this.data.isEditMode 
        });
        this.checkAllSelected();
      },
      complete: () => wx.hideNavigationBarLoading()
    });
  },

  // ✨ 1. 长按进入管理模式
  enterEditMode() {
    if (!this.data.isEditMode) {
      wx.vibrateShort(); // 给个手机震动反馈
      this.setData({ isEditMode: true, selectedIds: [], isAllSelected: false });
    }
  },

  // 退出管理模式
  exitEditMode() {
    this.setData({ isEditMode: false, selectedIds: [], isAllSelected: false });
  },

  // 监听复选框状态变化
  onCheckboxChange(e) {
    this.setData({ selectedIds: e.detail });
    this.checkAllSelected();
  },

  // 点击卡片直接选中/取消 (增强体验)
  toggleSingleCard(e) {
    if (!this.data.isEditMode) return; // 不在编辑模式下点击无效
    const id = e.currentTarget.dataset.id.toString();
    let ids = [...this.data.selectedIds];
    const index = ids.indexOf(id);
    if (index > -1) {
      ids.splice(index, 1);
    } else {
      ids.push(id);
    }
    this.setData({ selectedIds: ids });
    this.checkAllSelected();
  },

  // 判断是否已触发全选
  checkAllSelected() {
    const allSelected = this.data.orders.length > 0 && this.data.selectedIds.length === this.data.orders.length;
    this.setData({ isAllSelected: allSelected });
  },

  // ✨ 2. 点击全选按钮
  selectAll() {
    if (this.data.isAllSelected) {
      this.setData({ selectedIds: [], isAllSelected: false }); // 反选
    } else {
      const allIds = this.data.orders.map(item => item.id.toString());
      this.setData({ selectedIds: allIds, isAllSelected: true }); // 全选
    }
  },

  // ✨ 3. 批量删除选中记录
  deleteSelected() {
    const { selectedIds } = this.data;
    if (selectedIds.length === 0) return;

    wx.showModal({
      title: '确认删除',
      content: `确定要删除这 ${selectedIds.length} 条记录吗？`,
      confirmColor: '#ee0a24',
      success: (res) => {
        if (res.confirm) {
          wx.showLoading({ title: '删除中...' });
          
          // 循环生成删除请求并发起
          const deletePromises = selectedIds.map(id => {
            return new Promise((resolve) => {
              wx.request({
                url: `https://bd8d882.r9.vip.cpolar.cn/api/orders/${id}`,
                method: 'DELETE',
                success: resolve,
                fail: resolve
              });
            });
          });

          // 等待所有删除请求完成
          Promise.all(deletePromises).then(() => {
            wx.hideLoading();
            wx.showToast({ title: '已删除', icon: 'success' });
            this.setData({ selectedIds: [], isAllSelected: false });
            this.fetchOrders(); // 刷新列表
          });
        }
      }
    });
  }
});