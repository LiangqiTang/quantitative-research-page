/**
 * Vercel Cron Job - 每日量化报告生成
 * 触发时间: 每天UTC时间0点 (北京时间8点)
 */

const { spawnSync } = require('child_process');
const path = require('path');

export default async function handler(request, response) {
  try {
    // 验证请求源
    const authHeader = request.headers.get('authorization');
    if (authHeader !== `Bearer ${process.env.CRON_SECRET}`) {
      return response.status(401).json({ success: false, message: 'Unauthorized' });
    }

    // 执行Python脚本
    console.log('开始生成量化报告...');

    const result = spawnSync(
      process.execPath,
      [path.resolve(process.cwd(), 'main.py')],
      {
        stdio: 'pipe',
        encoding: 'utf-8',
        env: {
          ...process.env,
          PYTHONPATH: process.cwd()
        }
      }
    );

    // 处理输出
    if (result.stdout) {
      console.log('脚本输出:', result.stdout);
    }

    if (result.stderr) {
      console.error('脚本错误输出:', result.stderr);
    }

    if (result.status !== 0) {
      throw new Error(`脚本执行失败，退出码: ${result.status}`);
    }

    console.log('量化报告生成完成');
    response.status(200).json({
      success: true,
      message: '量化报告生成成功',
      output: result.stdout.trim(),
      error: result.stderr.trim()
    });

  } catch (error) {
    console.error('生成量化报告时出错:', error);
    response.status(500).json({
      success: false,
      message: '生成量化报告失败',
      error: error.message
    });
  }
}

export const config = {
  runtime: 'nodejs',
  memory: 3008,
  timeoutSeconds: 900
};