Page({
  data: {
    orders: [],
    isEditMode: false,
    selectedIds: [],
    isAllSelected: false,
    stepsConfig: [
      { text: '已接单', desc: '运维工程师 王师傅 已接单，正赶往现场' },
      { text: '排查维修中', desc: '工程师正在排查处理相关问题' },
      { text: '已完成', desc: '设备已恢复正常运行' }
    ]
  },

  onShow() {
    this.fetchOrders();
  },

  fetchOrders() {
    const savedOrders = wx.getStorageSync('om_orders') || [];
    this.setData({ 
      orders: savedOrders,
      // 如果数据删空了，自动退出编辑模式
      isEditMode: savedOrders.length === 0 ? false : this.data.isEditMode
    });
    this.checkAllSelected();
  },

  // ✨ 核心机制：统一处理整个卡片的点击
  onCardTap(e) {
    if (this.data.isEditMode) {
      // 1. 编辑模式下：点击卡片用于勾选/反选
      const id = e.currentTarget.dataset.id.toString();
      let ids = [...this.data.selectedIds];
      const index = ids.indexOf(id);
      if (index > -1) ids.splice(index, 1);
      else ids.push(id);
      this.setData({ selectedIds: ids });
      this.checkAllSelected();
    } else {
      // 2. 普通模式下：点击卡片用于推进进度
      const index = e.currentTarget.dataset.index;
      let orders = this.data.orders;
      
      if (orders[index].status < 2) {
        wx.vibrateShort(); // 手机微微震动反馈
        
        orders[index].status += 1;
        this.setData({ orders: orders });
        wx.setStorageSync('om_orders', orders); // 将最新进度同步存入缓存
        
        if (orders[index].status === 2) {
          wx.showToast({ title: '设备已修复', icon: 'success' });
        }
      }
    }
  },

  // --- 多选删除逻辑 (纯本地缓存操作) ---
  enterEditMode() {
    if (!this.data.isEditMode) {
      wx.vibrateShort();
      this.setData({ isEditMode: true, selectedIds: [], isAllSelected: false });
    }
  },
  
  exitEditMode() { this.setData({ isEditMode: false, selectedIds: [], isAllSelected: false }); },
  
  onCheckboxChange(e) { this.setData({ selectedIds: e.detail }); this.checkAllSelected(); },
  
  checkAllSelected() {
    const all = this.data.orders.length > 0 && this.data.selectedIds.length === this.data.orders.length;
    this.setData({ isAllSelected: all });
  },
  
  selectAll() {
    if (this.data.isAllSelected) {
      this.setData({ selectedIds: [], isAllSelected: false });
    } else {
      const allIds = this.data.orders.map(item => item.id.toString());
      this.setData({ selectedIds: allIds, isAllSelected: true });
    }
  },
  
  deleteSelected() {
    const { selectedIds } = this.data;
    if (selectedIds.length === 0) return;

    wx.showModal({
      title: '确认删除',
      content: `确定要删除这 ${selectedIds.length} 条工单记录吗？`,
      confirmColor: '#ee0a24',
      success: (res) => {
        if (res.confirm) {
          wx.showLoading({ title: '删除中...' });
          
          // 从本地缓存中过滤掉已被选中的订单
          let savedOrders = wx.getStorageSync('om_orders') || [];
          savedOrders = savedOrders.filter(order => !selectedIds.includes(order.id.toString()));
          
          // 更新本地缓存
          wx.setStorageSync('om_orders', savedOrders);

          // 模拟微小的延迟，让交互更加平滑自然
          setTimeout(() => {
            wx.hideLoading();
            wx.showToast({ title: '已删除', icon: 'success' });
            this.setData({ selectedIds: [], isAllSelected: false });
            this.fetchOrders(); // 刷新列表渲染
          }, 300);
        }
      }
    });
  }
});