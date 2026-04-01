Page({
  data: {
    product: {} // 存放商品数据
  },

  // 页面加载时触发，options 包含了上个页面传来的参数
  onLoad(options) {
    const productId = options.id; // 获取 id
    if (productId) {
      this.fetchDetail(productId);
    }
  },

  fetchDetail(id) {
    wx.showLoading({ title: '加载中' });
    wx.request({
      url: `https://bd8d882.r9.vip.cpolar.cn/api/products/${id}`, // 注意这里用了反引号
      success: (res) => {
        console.log("详情数据：", res.data);
        this.setData({ product: res.data.data });
      },
      complete: () => wx.hideLoading()
    })
  },

  addToCart() {
    wx.showToast({ title: '加入成功', icon: 'success' });
    // 下一步我们要在这里写真正的逻辑
  },

  buyNow() {
    wx.showToast({ title: '老板去上厕所了', icon: 'none' });
  }
})