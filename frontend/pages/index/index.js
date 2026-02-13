Page({
  data: {
    // 轮播图数据（暂时写死）
    banners: [
      'https://img.yzcdn.cn/vant/cat.jpeg', 
      'https://img.yzcdn.cn/vant/apple-1.jpg'
    ],
    // 商品列表（初始为空，等待后端填充）
    products: [] 
  },

  onLoad() {
    this.fetchProducts();
  },

  // 向 Python 后端请求数据
  fetchProducts() {
    wx.showLoading({ title: '加载商品中...' });
    
    wx.request({
      // 注意：必须和 main.py 里的地址一致
      url: 'http://127.0.0.1:8000/api/products', 
      method: 'GET',
      success: (res) => {
        console.log('收到后端数据:', res.data);
        // 把数据存入页面，界面会自动更新
        this.setData({
          products: res.data.data
        });
      },
      fail: (err) => {
        console.error('请求失败:', err);
        wx.showToast({ title: '连接后端失败', icon: 'none' });
      },
      complete: () => {
        wx.hideLoading();
      }
    })
  },

  // ... data, onLoad, fetchProducts ...

// 跳转详情页
  goToDetail(e) {
    // 拿到被点击商品的 id
    const id = e.currentTarget.dataset.id;
    wx.navigateTo({
      url: `/pages/goods/goods?id=${id}`, // 把 id 传给详情页
    });
  }
})