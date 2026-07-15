/**
 * AI知库 - 翡翠匹配整合版
 * 小程序全局逻辑
 * 负责初始化全局数据、存储检查、系统信息获取和登录状态管理
 * 
 * 用户角色：
 * - 用户端：使用AI知库功能（知识库问答）
 * - 商家端：使用翡翠匹配平台功能（产品管理、客户管理）
 */

const storage = require('./utils/storage')
const { setupGlobalErrorHandler } = require('./utils/error-handler')

App({
  onLaunch() {
    // 初始化全局错误处理
    setupGlobalErrorHandler()

    // 系统信息
    this.globalData.systemInfo = wx.getSystemInfoSync()

    // 初始化存储
    this.initStorage()
    this.initMockData()

    // 加载用户状态
    this.globalData.isLoggedIn = storage.getLoginStatus()
    this.globalData.userPhone = storage.getUserPhone()
    this.globalData.userName = storage.getUserName() || '翡翠爱好者'
    this.globalData.userRole = storage.getUserRole()
    this.globalData.token = storage.getToken()

    // 更新tabBar未读消息角标
    this.updateTabBarBadge()
  },

  onShow() {
    this.updateTabBarBadge()
  },

  initStorage() {
    const keys = [
      { key: 'api_key', default: '' },
      { key: 'api_base_url', default: 'https://api.openai.com/v1' },
      { key: 'knowledge_bases', default: '[]' },
      { key: 'chat_history', default: '{}' },
      { key: 'user_role', default: 'customer' },
      { key: 'products', default: '[]' },
      { key: 'merchant_products', default: '[]' },
      { key: 'customers', default: '[]' },
      { key: 'merchant_vip', default: '' },
      { key: 'user_messages', default: '[]' },
      { key: 'search_history', default: '[]' },
      { key: 'favorites', default: '[]' },
      { key: 'user_token', default: '' }
    ]

    keys.forEach(({ key, default: def }) => {
      if (!wx.getStorageSync(key) && wx.getStorageSync(key) !== false) {
        wx.setStorageSync(key, def)
      }
    })
  },

  initMockData() {
    const productPool = storage.getProductPool()
    if (!productPool || productPool.length === 0) {
      const mockProducts = [
        {
          id: 'p001',
          name: '冰种帝王绿翡翠吊坠',
          category: '吊坠',
          price: 88000,
          description: '冰种质地，帝王绿色泽，通透温润，雕工精美。',
          images: [],
          specs: {
            zhonglei: '翡翠',
            zhongshui: '冰种',
            yanse: '帝王绿',
            chidu: '32x18x6mm',
            zhongliang: '12.5g',
            chandi: '缅甸'
          },
          merchantId: 'm001',
          merchantName: '翠玉轩'
        },
        {
          id: 'p002',
          name: '玻璃种阳绿翡翠手镯',
          category: '手镯',
          price: 156000,
          description: '玻璃种质地，阳绿色泽，通透度极高，收藏级品质。',
          images: [],
          specs: {
            zhonglei: '翡翠',
            zhongshui: '玻璃种',
            yanse: '阳绿',
            neijing: '58mm',
            zhongliang: '52.3g',
            chandi: '缅甸'
          },
          merchantId: 'm002',
          merchantName: '御翠坊'
        },
        {
          id: 'p003',
          name: '糯种满绿翡翠戒指',
          category: '戒指',
          price: 32000,
          description: '糯种质地，满绿色泽，饱满圆润，佩戴典雅。',
          images: [],
          specs: {
            zhonglei: '翡翠',
            zhongshui: '糯种',
            yanse: '满绿',
            chundu: '12x10mm',
            quanhao: '17号',
            chandi: '缅甸'
          },
          merchantId: 'm001',
          merchantName: '翠玉轩'
        }
      ]
      storage.setProductPool(mockProducts)
    }

    const customerPool = storage.getCustomerPool()
    if (!customerPool || customerPool.length === 0) {
      const mockCustomers = [
        {
          id: 'c001',
          name: '张先生',
          phone: '138****8888',
          budget: '50000-100000',
          category: '吊坠',
          description: '求购冰种绿色翡翠吊坠，预算5-10万。',
          createTime: '2025-01-10 14:30',
          status: 'pending'
        },
        {
          id: 'c002',
          name: '李女士',
          phone: '139****6666',
          budget: '100000-200000',
          category: '手镯',
          description: '求购阳绿翡翠手镯，内径57-58mm，预算10-20万。',
          createTime: '2025-01-09 10:15',
          status: 'pending'
        },
        {
          id: 'c003',
          name: '王先生',
          phone: '136****9999',
          budget: '20000-50000',
          category: '戒指',
          description: '求购翡翠戒指，男士款，预算2-5万。',
          createTime: '2025-01-08 16:45',
          status: 'matched'
        }
      ]
      storage.setCustomerPool(mockCustomers)
    }
  },

  globalData: {
    apiKey: '',
    apiBaseUrl: 'https://api.openai.com/v1',
    systemInfo: null,
    isLoggedIn: false,
    userPhone: '',
    userName: '翡翠爱好者',
    userRole: 'customer',
    token: '',
    currentSessionId: null
  },

  setUserRole(role) {
    this.globalData.userRole = role
    wx.setStorageSync('user_role', role)
  },

  getUserRole() {
    return this.globalData.userRole
  },

  /**
   * 更新TabBar消息角标
   */
  updateTabBarBadge() {
    try {
      const raw = wx.getStorageSync('user_messages')
      const messages = raw ? (typeof raw === 'string' ? JSON.parse(raw) : raw) : []
      const unreadCount = messages.filter(m => m.unread).length

      if (unreadCount > 0) {
        wx.setTabBarBadge({
          index: 2,
          text: String(unreadCount > 99 ? '99+' : unreadCount)
        })
      } else {
        wx.removeTabBarBadge({ index: 2 })
      }
    } catch (e) {
      // 静默处理
    }
  },

  /**
   * 设置全局登录状态
   */
  setLoginState({ isLoggedIn, phone, name, token }) {
    this.globalData.isLoggedIn = isLoggedIn
    this.globalData.userPhone = phone || ''
    this.globalData.userName = name || '翡翠爱好者'
    this.globalData.token = token || ''

    storage.setLoginStatus(isLoggedIn)
    storage.setUserPhone(phone || '')
    storage.setUserName(name || '')
    storage.setToken(token || '')
  }
})
