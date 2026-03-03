/**
 * MiGPT-Next 配置文件（极空间 NAS 部署用）
 * 部署时复制为 config.js 并填写 speaker.userId、speaker.password、speaker.did
 * @type {import('@mi-gpt/next').MiGPTConfig}
 */
export default {
  debug: false,
  speaker: {
    did: '小米音响 Pro',  // 与米家/小爱里显示的设备名一致
    userId: '请填写你的小米ID',  // 小米 ID（一串数字），非手机号
    password: '请填写你的小米账号密码',
    // 若提示「本次登录需要验证码，请使用 passToken 重新登录」，必填：
    // 浏览器登录 https://account.xiaomi.com → F12 → Application → Cookies → 复制 passToken 的值
    passToken: '',  // 如：'V1:xxxxxxxx...'，注意保密
  },
  openai: {
    baseURL: 'https://api.openai.com/v1',
    apiKey: 'sk-placeholder',
    model: 'gpt-4o-mini',
  },
  prompt: {
    system: '你是一个智能助手，请根据用户的问题给出回答。',
  },
  context: {
    historyMaxLength: 10,
  },
  callAIKeywords: ['请', '你'],
  async onMessage(engine, { text }) {
    const t = (text || '').trim();
    const NAS_IP = '192.168.50.86';
    const BRIDGE = `http://${NAS_IP}:8765`;

    // 加湿器
    if (/打开加湿器|开启加湿器|加湿器开/.test(t)) {
      try {
        await fetch(`${BRIDGE}/jiashiqi/on`, { method: 'POST' });
        return { text: '好的，已打开加湿器。' };
      } catch (e) {
        return { text: '加湿器控制失败，请稍后再试。' };
      }
    }
    if (/关闭加湿器|加湿器关/.test(t)) {
      try {
        await fetch(`${BRIDGE}/jiashiqi/off`, { method: 'POST' });
        return { text: '好的，已关闭加湿器。' };
      } catch (e) {
        return { text: '加湿器控制失败，请稍后再试。' };
      }
    }

    // 新风机
    if (/打开新风机|开启新风|开新风机/.test(t)) {
      try {
        await fetch(`${BRIDGE}/xinfengji/on`, { method: 'POST' });
        return { text: '好的，已发送新风机控制指令，正在执行，请稍候。' };
      } catch (e) {
        return { text: '新风机控制失败，请稍后再试。' };
      }
    }
    if (/关闭新风机|关闭新风|关新风机/.test(t)) {
      try {
        await fetch(`${BRIDGE}/xinfengji/off`, { method: 'POST' });
        return { text: '好的，已发送关闭新风机指令，正在执行，请稍候。' };
      } catch (e) {
        return { text: '新风机控制失败，请稍后再试。' };
      }
    }

    return null;
  },
};
