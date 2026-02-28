Page({
  data: {
    currentPoints: 0,
    
    // 预设 6 款与农业、乡村生活强相关的兑换商品
    products: [
      { 
        id: 1, 
        name: '东北五常大米 10kg装', 
        shortName: '五常大米', 
        desc: '绿色有机，软糯香甜', 
        price: 800, 
        color: 'linear-gradient(135deg, #f6d365 0%, #fda085 100%)' // 暖橙色系
      },
      { 
        id: 2, 
        name: '农家压榨纯菜籽油 5L', 
        shortName: '纯菜籽油', 
        desc: '物理压榨，炒菜倍香', 
        price: 600, 
        color: 'linear-gradient(135deg, #e6b980 0%, #eacda3 100%)' // 金黄色系
      },
      { 
        id: 3, 
        name: '高效有机复合肥 20kg', 
        shortName: '有机肥料', 
        desc: '促进增产，改良土壤', 
        price: 500, 
        color: 'linear-gradient(135deg, #84fab0 0%, #8fd3f4 100%)' // 青绿色系
      },
      { 
        id: 4, 
        name: '春耕农用加厚地膜 1卷', 
        shortName: '农用地膜', 
        desc: '保温保湿，防草抗旱', 
        price: 300, 
        color: 'linear-gradient(135deg, #a18cd1 0%, #fbc2eb 100%)' // 紫色系
      },
      { 
        id: 5, 
        name: '优质高产蔬菜种子盲盒', 
        shortName: '蔬菜种子', 
        desc: '含番茄、黄瓜、白菜等', 
        price: 150, 
        color: 'linear-gradient(135deg, #11998e 0%, #38ef7d 100%)' // 纯绿色系
      },
      { 
        id: 6, 
        name: '三大运营商 50元话费卡', 
        shortName: '50元话费', 
        desc: '全国通用，即时到账', 
        price: 500, 
        color: 'linear-gradient(135deg, #ff9a9e 0%, #fecfef 100%)' // 粉红色系
      }
    ]
  },

  onShow() {
    this.fetchLocalPoints();
  },

  // 获取当前的积分余额
  fetchLocalPoints() {
    const pts = wx.getStorageSync('carbonPoints') || 150; // 默认给150分启动资金
    this.setData({ currentPoints: pts });
  },

  // ✨ 核心逻辑：兑换商品
  buyProduct(e) {
    const productId = e.currentTarget.dataset.id;
    const product = this.data.products.find(p => p.id === productId);
    
    if (!product) return;

    // 1. 判断余额是否充足
    if (this.data.currentPoints < product.price) {
      return wx.showToast({
        title: '积分不足，快去做任务赚积分吧！',
        icon: 'none',
        duration: 2000
      });
    }

    // 2. 弹窗二次确认
    wx.showModal({
      title: '确认兑换',
      content: `确定使用 ${product.price} 积分兑换【${product.name}】吗？`,
      success: (res) => {
        if (res.confirm) {
          wx.showLoading({ title: '兑换中...' });
          
          // 模拟网络延迟
          setTimeout(() => {
            wx.hideLoading();
            
            // 3. 扣除积分，保存本地缓存
            const newPoints = this.data.currentPoints - product.price;
            wx.setStorageSync('carbonPoints', newPoints);
            
            // 4. 刷新页面显示余额
            this.setData({ currentPoints: newPoints });

            wx.showToast({
              title: '兑换成功！农资将配送至您绑定的村地址',
              icon: 'none',
              duration: 3000
            });
          }, 800);
        }
      }
    });
  }
});