import * as echarts from '../../ec-canvas/echarts';

let chartPie = null;
let chartBar = null;

Page({
  data: {
    ecPie: { lazyLoad: true },
    ecBar: { lazyLoad: true },
    currentData: {},
    withdrawableAmount: '0.00', // ✨ 新增：独立控制展示的余额
    
    activeStep: 1, 
    steps: [
      { text: '待审核', desc: '电网核对电量' },
      { text: '结算中', desc: '财务打款中' },
      { text: '已到账', desc: '收益可提现' }
    ]
  },

  onShow() {
    this.pieComponent = this.selectComponent('#mychart-dom-pie');
    this.barComponent = this.selectComponent('#mychart-dom-bar');
    this.fetchRealDataAndRender();
  },

  fetchRealDataAndRender() {
    // ✨ 1. 拿取本地的身份证
    const myOpenId = wx.getStorageSync('user_openid');
    if (!myOpenId) {
      // 未登录状态下，可以给个空数据或者直接拦截
      return; 
    }

    wx.showNavigationBarLoading();
    wx.request({
      url: 'https://466eb478.r7.cpolar.cn/api/surplus',
      method: 'GET',
      // ✨ 2. 塞入请求头
      header: { 'x-wx-openid': myOpenId },
      success: (res) => {
        if (res.data.error) {
           return wx.showToast({ title: res.data.error, icon: 'none' });
        }
        
        const todayData = res.data.today_data;
        const chartDataArray = res.data.chart_data;

        const hasWithdrawn = wx.getStorageSync('hasWithdrawnToday');

        this.setData({
          currentData: todayData,
          withdrawableAmount: hasWithdrawn ? '0.00' : todayData.income
        }, () => {
          // 在 setData 的回调里，或者用 setTimeout 稍微延迟一下画图
          setTimeout(() => {
            this.initPieChart(todayData.selfUse, todayData.surplus);
            this.initBarChart(chartDataArray);
          }, 50);
        });

        this.initPieChart(todayData.selfUse, todayData.surplus);
        this.initBarChart(chartDataArray);
      },
      fail: () => {
        wx.showToast({ title: '网络有些慢，请重试', icon: 'none' });
      },
      complete: () => wx.hideNavigationBarLoading()
    });
  },

  initPieChart(selfUse, surplus) {
    this.pieComponent.init((canvas, width, height, dpr) => {
      chartPie = echarts.init(canvas, null, { width, height, devicePixelRatio: dpr });
      canvas.setChart(chartPie);
      
      const option = {
        color: ['#1989fa', '#07c160'],
        tooltip: { trigger: 'item', formatter: '{b}: {d}%' },
        legend: { bottom: '0', icon: 'circle', itemWidth: 10, itemHeight: 10 },
        series: [{
          type: 'pie',
          radius: ['40%', '70%'],
          avoidLabelOverlap: false,
          label: { show: false, position: 'center' },
          labelLine: { show: false },
          data: [
            { value: surplus, name: '余电上网' },
            { value: selfUse, name: '自发自用' }
          ]
        }]
      };
      chartPie.setOption(option);
      return chartPie;
    });
  },

  // ✨ 核心修改：渲染后端传来的真实日期数组
  initBarChart(chartDataArray) {
    this.barComponent.init((canvas, width, height, dpr) => {
      chartBar = echarts.init(canvas, null, { width, height, devicePixelRatio: dpr });
      canvas.setChart(chartBar);
      
      const days = [];
      const incomeData = [];
      const savedData = [];
      
      // 解析后端传回的 5 天数据
      chartDataArray.forEach((item, index) => {
        if (index === chartDataArray.length - 1) {
          days.push('今日');
        } else {
          // 将 YYYY-MM-DD 转为 MM/DD
          const parts = item.date.split('-');
          days.push(`${parseInt(parts[1])}/${parseInt(parts[2])}`);
        }
        incomeData.push(item.income);
        savedData.push(item.saved);
      });

      const option = {
        grid: { left: '3%', right: '4%', bottom: '12%', top: '15%', containLabel: true },
        tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
        legend: { data: ['上网收益', '省钱费用'], bottom: 0, itemWidth: 10, itemHeight: 10, icon: 'circle' },
        xAxis: { type: 'category', data: days, axisLine: { lineStyle: { color: '#999' } } },
        yAxis: { type: 'value', name: '金额(元)' },
        series: [
          {
            name: '上网收益',
            type: 'bar',
            stack: 'total', 
            barWidth: '40%',
            itemStyle: { color: '#1989fa' },
            data: incomeData
          },
          {
            name: '省钱费用',
            type: 'bar',
            stack: 'total',
            barWidth: '40%',
            itemStyle: { color: '#07c160', borderRadius: [4, 4, 0, 0] },
            data: savedData
          }
        ]
      };
      chartBar.setOption(option);
      return chartBar;
    });
  },

// ✨ 跳转到提现记录页
goToWithdrawList() {
  wx.navigateTo({ url: '/pages/withdraw_list/withdraw_list' });
},

// ✨ 调用后端保存提现记录
  applyWithdraw() {
    const amount = parseFloat(this.data.withdrawableAmount);
    if (amount <= 0) {
      return wx.showToast({ title: '暂无可提现余额', icon: 'none' });
    }

    // ✨ 1. 提现前必须校验身份
    const myOpenId = wx.getStorageSync('user_openid');
    if (!myOpenId) {
      return wx.showToast({ title: '请先前往我的页面登录', icon: 'none' });
    }

    wx.showModal({
      title: '提现确认',
      content: `确定将 ¥${amount} 提现至绑定的银行卡吗？`,
      success: (res) => {
        if (res.confirm) {
          wx.showLoading({ title: '申请中...' });
          wx.request({
            url: 'https://466eb478.r7.cpolar.cn/api/withdraw',
            method: 'POST',
            // ✨ 2. 塞入请求头，告诉后端是谁在提现
            header: { 'x-wx-openid': myOpenId },
            data: { amount: amount },
            success: (wRes) => {
              if (wRes.data.status === 'success') {
                wx.showToast({ title: '提现申请已提交', icon: 'success' });
                wx.setStorageSync('hasWithdrawnToday', true);
                this.setData({ withdrawableAmount: '0.00', activeStep: 0 });
              } else {
                wx.showToast({ title: wRes.data.error || '提现失败', icon: 'none' });
              }
            },
            complete: () => wx.hideLoading()
          });
        }
      }
    });
  }
});