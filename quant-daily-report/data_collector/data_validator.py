"""
数据质量验证器
负责对采集到的数据进行多维度质量验证
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

class DataQualityValidator:
    """数据质量验证器"""

    def __init__(self):
        self.required_fields = {
            'basic': ['symbol', 'name', 'industry', 'list_date'],
            'kline': ['open', 'high', 'low', 'close', 'volume', 'amount'],
            'financial': ['pe', 'pb', 'eps', 'revenue', 'profit']
        }

    def validate_all(self, data: Dict) -> Dict:
        """
        全面数据质量验证
        :param data: 待验证数据
        :return: 验证结果报告
        """
        report = {
            'overall_score': 0,
            'passed': False,
            'checks': [],
            'errors': [],
            'warnings': [],
            'suggestions': []
        }

        try:
            # 执行各种检查
            checks = [
                ('basic_fields', '基本字段检查', self._check_basic_fields, 20),
                ('kline_data', 'K线数据检查', self._check_kline_data, 30),
                ('financial_data', '财务数据检查', self._check_financial_data, 20),
                ('data_rationality', '数据合理性检查', self._check_data_rationality, 15),
                ('data_consistency', '数据一致性检查', self._check_data_consistency, 15),
            ]

            total_score = 0
            max_total_score = sum(weight for _, _, _, weight in checks)

            for check_id, check_name, check_func, weight in checks:
                try:
                    score, passed, errors, warnings = check_func(data)
                    total_score += score

                    report['checks'].append({
                        'id': check_id,
                        'name': check_name,
                        'score': score,
                        'max_score': weight,
                        'passed': passed,
                        'errors': errors,
                        'warnings': warnings
                    })

                    report['errors'].extend(errors)
                    report['warnings'].extend(warnings)

                except Exception as e:
                    report['errors'].append(f"{check_name}执行失败: {e}")
                    report['checks'].append({
                        'id': check_id,
                        'name': check_name,
                        'score': 0,
                        'max_score': weight,
                        'passed': False,
                        'errors': [f"执行失败: {e}"],
                        'warnings': []
                    })

            # 计算总分
            report['overall_score'] = total_score
            report['passed'] = total_score >= max_total_score * 0.7  # 70分及格

            # 生成建议
            report['suggestions'] = self._generate_suggestions(report)

            return report

        except Exception as e:
            report['errors'].append(f"整体验证失败: {e}")
            return report

    def _check_basic_fields(self, data: Dict) -> (float, bool, List[str], List[str]):
        """检查基本字段"""
        errors = []
        warnings = []
        max_score = 20
        score = max_score

        # 检查基本信息
        if 'basic' not in data:
            errors.append("缺少basic字段")
            score = 0
        else:
            basic_data = data['basic']
            for field in self.required_fields['basic']:
                if field not in basic_data or basic_data.get(field) in [None, '', 0]:
                    errors.append(f"基本信息缺少{field}字段")
                    score -= 5

        # 检查是否有symbol字段
        if not data.get('symbol'):
            errors.append("缺少symbol字段")
            score -= 5

        # 检查是否有name字段
        if not data.get('name'):
            errors.append("缺少name字段")
            score -= 5

        score = max(0, score)
        passed = score >= max_score * 0.7

        return score, passed, errors, warnings

    def _check_kline_data(self, data: Dict) -> (float, bool, List[str], List[str]):
        """检查K线数据质量"""
        errors = []
        warnings = []
        max_score = 30
        score = max_score

        if 'kline' not in data:
            errors.append("缺少kline字段")
            score = 0
            return score, False, errors, warnings

        kline_data = data['kline']

        # 检查K线数据是否为空
        if kline_data is None or kline_data.empty:
            errors.append("K线数据为空")
            score = 0
            return score, False, errors, warnings

        # 检查必要字段
        for field in self.required_fields['kline']:
            if field not in kline_data.columns:
                errors.append(f"K线数据缺少{field}字段")
                score -= 5

        # 检查数据量
        min_days = 30  # 至少需要30天数据
        if len(kline_data) < min_days:
            warnings.append(f"K线数据量较少 ({len(kline_data)}天)")
            score -= 3

        # 检查数据类型
        try:
            numeric_cols = ['open', 'high', 'low', 'close', 'volume', 'amount']
            for col in numeric_cols:
                if col in kline_data.columns:
                    kline_data[col] = pd.to_numeric(kline_data[col], errors='coerce')
                    if kline_data[col].isnull().any():
                        errors.append(f"K线数据{col}列包含非数值")
                        score -= 3
        except Exception as e:
            errors.append(f"K线数据类型检查失败: {e}")
            score -= 10

        score = max(0, score)
        passed = score >= max_score * 0.7

        return score, passed, errors, warnings

    def _check_financial_data(self, data: Dict) -> (float, bool, List[str], List[str]):
        """检查财务数据质量"""
        errors = []
        warnings = []
        max_score = 20
        score = max_score

        if 'financial' not in data:
            warnings.append("缺少financial字段")
            score = max_score * 0.5
            return score, True, errors, warnings

        financial_data = data['financial']

        # 检查关键财务指标
        key_metrics = ['pe', 'pb', 'eps']
        for metric in key_metrics:
            if metric not in financial_data or financial_data.get(metric) in [None, 0]:
                warnings.append(f"财务数据缺少{metric}字段")
                score -= 3

        # 检查财务指标合理性
        try:
            if 'pe' in financial_data:
                pe = financial_data['pe']
                if pe < 0 or pe > 500:
                    warnings.append(f"市盈率异常: {pe}")
                    score -= 2

            if 'pb' in financial_data:
                pb = financial_data['pb']
                if pb < 0 or pb > 100:
                    warnings.append(f"市净率异常: {pb}")
                    score -= 2

            if 'eps' in financial_data:
                eps = financial_data['eps']
                if abs(eps) > 100:
                    warnings.append(f"每股收益异常: {eps}")
                    score -= 2

        except Exception as e:
            errors.append(f"财务指标合理性检查失败: {e}")
            score -= 5

        score = max(0, score)
        passed = score >= max_score * 0.7

        return score, passed, errors, warnings

    def _check_data_rationality(self, data: Dict) -> (float, bool, List[str], List[str]):
        """检查数据合理性"""
        errors = []
        warnings = []
        max_score = 15
        score = max_score

        try:
            if 'kline' in data and not data['kline'].empty:
                kline = data['kline'].copy()

                # 检查价格关系
                price_checks = [
                    ('high >= close', kline['high'] >= kline['close'], '最高价小于收盘价'),
                    ('low <= close', kline['low'] <= kline['close'], '最低价大于收盘价'),
                    ('high >= low', kline['high'] >= kline['low'], '最高价小于最低价'),
                    ('close >= 0', kline['close'] >= 0, '收盘价为负数'),
                ]

                for check_name, check_condition, error_msg in price_checks:
                    if not check_condition.all():
                        error_count = len(kline[~check_condition])
                        errors.append(f"{error_msg}: {error_count}条记录")
                        score -= 3

                # 检查成交量
                if 'volume' in kline.columns:
                    if (kline['volume'] < 0).any():
                        error_count = len(kline[kline['volume'] < 0])
                        errors.append(f"成交量为负数: {error_count}条记录")
                        score -= 3

                    if (kline['volume'] == 0).sum() > len(kline) * 0.1:
                        warning_count = len(kline[kline['volume'] == 0])
                        warnings.append(f"大量零成交量记录: {warning_count}条")
                        score -= 2

                # 检查涨跌幅
                if 'pctChg' in kline.columns:
                    abnormal_chg = abs(kline['pctChg']) > 20  # 涨跌幅超过20%
                    if abnormal_chg.any():
                        warning_count = len(kline[abnormal_chg])
                        warnings.append(f"异常涨跌幅记录: {warning_count}条")
                        score -= 2

        except Exception as e:
            errors.append(f"数据合理性检查失败: {e}")
            score -= 8

        score = max(0, score)
        passed = score >= max_score * 0.7

        return score, passed, errors, warnings

    def _check_data_consistency(self, data: Dict) -> (float, bool, List[str], List[str]):
        """检查数据一致性"""
        errors = []
        warnings = []
        max_score = 15
        score = max_score

        try:
            # 检查数据更新时间一致性
            update_times = []
            if 'update_time' in data:
                update_times.append(('main', data['update_time']))
            if 'basic' in data and 'update_time' in data['basic']:
                update_times.append(('basic', data['basic']['update_time']))
            if 'kline' in data and 'update_time' in data['kline']:
                update_times.append(('kline', data['kline']['update_time']))

            if len(update_times) > 1:
                main_time = update_times[0][1]
                for source, update_time in update_times[1:]:
                    time_diff = abs((main_time - update_time).total_seconds())
                    if time_diff > 3600:  # 超过1小时
                        warnings.append(f"{source}数据更新时间差异过大: {time_diff/3600:.1f}小时")
                        score -= 2

            # 检查价格与涨跌幅的一致性
            if 'kline' in data and not data['kline'].empty:
                kline = data['kline'].copy()
                if 'pctChg' in kline.columns and 'close' in kline.columns and 'preclose' in kline.columns:
                    # 计算理论涨跌幅
                    kline['pctChg_calc'] = (kline['close'] - kline['preclose']) / kline['preclose'] * 100
                    # 允许0.1%的误差
                    diff = abs(kline['pctChg'] - kline['pctChg_calc'])
                    inconsistent = diff > 0.1
                    if inconsistent.any():
                        error_count = len(kline[inconsistent])
                        warnings.append(f"涨跌幅数据不一致: {error_count}条记录")
                        score -= 3

        except Exception as e:
            errors.append(f"数据一致性检查失败: {e}")
            score -= 5

        score = max(0, score)
        passed = score >= max_score * 0.7

        return score, passed, errors, warnings

    def _generate_suggestions(self, report: Dict) -> List[str]:
        """生成改进建议"""
        suggestions = []

        if not report['passed']:
            suggestions.append("数据质量未通过，建议重新获取或使用备用数据源")

        # 根据错误类型生成建议
        error_keywords = {
            '缺少字段': '检查数据源接口是否有字段变更',
            '数据为空': '检查数据源是否正常返回数据',
            '非数值': '检查数据类型转换逻辑',
            '价格关系': '检查数据采集过程中是否有数据损坏',
            '成交量': '检查成交量字段是否正确映射',
            '涨跌幅': '检查涨跌幅计算公式是否正确',
            '财务指标': '检查财务数据接口是否正常',
        }

        for error in report['errors']:
            for keyword, suggestion in error_keywords.items():
                if keyword in error:
                    suggestions.append(suggestion)
                    break

        # 根据得分情况生成建议
        overall_score = report['overall_score']
        if overall_score < 50:
            suggestions.append("数据质量较差，建议全面检查数据采集流程")
        elif overall_score < 70:
            suggestions.append("数据质量一般，建议重点改进低得分项")
        elif overall_score < 90:
            suggestions.append("数据质量良好，建议持续监控数据质量")
        else:
            suggestions.append("数据质量优秀，继续保持")

        # 去重建议
        return list(set(suggestions))

    def calculate_data_quality_score(self, data: Dict) -> float:
        """
        计算数据质量综合得分
        :param data: 待评估数据
        :return: 0-100的得分
        """
        report = self.validate_all(data)
        return report['overall_score']

    def is_data_acceptable(self, data: Dict, min_score: float = 70) -> bool:
        """
        判断数据是否可接受
        :param data: 待评估数据
        :param min_score: 最低可接受分数
        :return: 是否可接受
        """
        score = self.calculate_data_quality_score(data)
        return score >= min_score

    def generate_quality_report(self, data: Dict, symbol: str = '') -> str:
        """
        生成数据质量报告
        :param data: 待评估数据
        :param symbol: 股票代码
        :return: 文本格式的报告
        """
        report = self.validate_all(data)

        report_text = f"""📊 数据质量验证报告

股票代码: {symbol}
验证时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

📈 总体评估
综合得分: {report['overall_score']}/100
验证结果: {'✅ 通过' if report['passed'] else '❌ 未通过'}

🔍 分项检查结果
"""

        for check in report['checks']:
            status = '✅' if check['passed'] else '❌'
            report_text += f"{status} {check['name']}: {check['score']}/{check['max_score']}\n"

        if report['errors']:
            report_text += "\n❌ 发现问题:\n"
            for i, error in enumerate(report['errors'], 1):
                report_text += f"  {i}. {error}\n"

        if report['warnings']:
            report_text += "\n⚠️ 警告:\n"
            for i, warning in enumerate(report['warnings'], 1):
                report_text += f"  {i}. {warning}\n"

        if report['suggestions']:
            report_text += "\n💡 改进建议:\n"
            for i, suggestion in enumerate(report['suggestions'], 1):
                report_text += f"  {i}. {suggestion}\n"

        return report_text

if __name__ == "__main__":
    # 测试代码
    validator = DataQualityValidator()

    # 创建测试数据
    test_data = {
        'symbol': '000001',
        'name': '平安银行',
        'basic': {
            'symbol': '000001',
            'name': '平安银行',
            'industry': '银行',
            'list_date': '1991-04-03',
            'update_time': datetime.now()
        },
        'kline': pd.DataFrame({
            'open': [10.0, 10.2, 10.1],
            'high': [10.3, 10.4, 10.2],
            'low': [9.9, 10.1, 10.0],
            'close': [10.2, 10.3, 10.1],
            'volume': [10000, 12000, 9000],
            'amount': [102000, 123600, 90900],
            'preclose': [9.9, 10.2, 10.3],
            'pctChg': [3.03, 0.98, -1.94]
        }),
        'financial': {
            'pe': 10.2,
            'pb': 1.1,
            'eps': 2.3,
            'revenue': 1500,
            'profit': 300
        },
        'update_time': datetime.now()
    }

    # 验证数据
    report = validator.validate_all(test_data)
    print(validator.generate_quality_report(test_data, '000001'))

    # 测试异常数据
    bad_data = {
        'symbol': '000001',
        'name': '平安银行',
        'kline': pd.DataFrame({
            'open': [10.0, 9.9],
            'high': [9.8, 10.0],  # 错误：最高价 < 最低价
            'low': [9.9, 9.8],
            'close': [9.9, 9.9],
            'volume': [10000, -5000],  # 错误：负成交量
            'amount': [99000, -49500]
        })
    }

    print("\n" + "="*60 + "\n")
    print(validator.generate_quality_report(bad_data, '000001'))