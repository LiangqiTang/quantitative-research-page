#!/usr/bin/env python3
"""
参数优化模块
使用遗传算法优化策略参数
"""

import numpy as np
import pandas as pd
import random
from copy import deepcopy
from datetime import datetime
import logging


class ParameterOptimizer:
    """参数优化器"""

    def __init__(self, backtester):
        self.logger = logging.getLogger('parameter_optimizer')
        self.backtester = backtester

        # 遗传算法参数
        self.population_size = 50
        self.generations = 20
        self.mutation_rate = 0.1
        self.crossover_rate = 0.7
        self.elitism_rate = 0.1

    def optimize_parameters(self, parameter_space, objective_func=None):
        """
        优化策略参数

        参数:
            parameter_space: 参数空间配置
            objective_func: 自定义目标函数

        返回:
            best_params: 最优参数
            optimization_history: 优化历史
        """
        self.logger.info("🔧 开始参数优化")
        self.logger.info(f"   参数空间: {parameter_space}")

        # 初始化种群
        population = self._initialize_population(parameter_space)

        # 设置目标函数
        if objective_func is None:
            objective_func = self._default_objective

        optimization_history = []

        for generation in range(self.generations):
            self.logger.info(f"📊 第 {generation+1}/{self.generations} 代优化")

            # 评估适应度
            fitness_scores = self._evaluate_population(population, objective_func, parameter_space)

            # 记录最好的结果
            best_idx = np.argmax(fitness_scores)
            best_fitness = fitness_scores[best_idx]
            best_params = population[best_idx]

            optimization_history.append({
                'generation': generation + 1,
                'best_fitness': best_fitness,
                'best_params': best_params,
                'avg_fitness': np.mean(fitness_scores),
                'std_fitness': np.std(fitness_scores)
            })

            self.logger.info(f"   最佳适应度: {best_fitness:.4f}")
            self.logger.info(f"   平均适应度: {np.mean(fitness_scores):.4f}")
            self.logger.info(f"   最优参数: {best_params}")

            # 生成新种群
            population = self._generate_new_population(population, fitness_scores)

            # 应用精英保留
            elite_size = int(self.elitism_rate * len(population))
            if elite_size > 0:
                elite_indices = np.argsort(fitness_scores)[-elite_size:]
                elite_individuals = [population[i] for i in elite_indices]
                population[:elite_size] = elite_individuals

        # 找到最优参数
        best_idx = np.argmax([history['best_fitness'] for history in optimization_history])
        best_params = optimization_history[best_idx]['best_params']
        best_fitness = optimization_history[best_idx]['best_fitness']

        self.logger.info("🎉 参数优化完成")
        self.logger.info(f"   最佳适应度: {best_fitness:.4f}")
        self.logger.info(f"   最优参数: {best_params}")

        return best_params, optimization_history

    def _initialize_population(self, parameter_space):
        """初始化种群"""
        population = []

        for _ in range(self.population_size):
            individual = {}
            for param_name, param_config in parameter_space.items():
                param_type = param_config.get('type', 'float')
                param_range = param_config.get('range', [0, 1])

                if param_type == 'float':
                    value = random.uniform(param_range[0], param_range[1])
                elif param_type == 'int':
                    value = random.randint(param_range[0], param_range[1])
                elif param_type == 'categorical':
                    value = random.choice(param_config.get('categories', []))
                elif param_type == 'bool':
                    value = random.choice([True, False])
                else:
                    value = random.uniform(param_range[0], param_range[1])

                # 应用参数步长
                if param_type in ['float', 'int'] and 'step' in param_config:
                    step = param_config['step']
                    value = round(value / step) * step

                individual[param_name] = value

            population.append(individual)

        return population

    def _evaluate_population(self, population, objective_func, parameter_space):
        """评估种群适应度"""
        fitness_scores = []

        for individual in population:
            try:
                # 验证参数有效性
                if not self._validate_parameters(individual, parameter_space):
                    fitness_scores.append(-np.inf)
                    continue

                # 计算适应度
                fitness = objective_func(self.backtester, individual)
                fitness_scores.append(fitness)

            except Exception as e:
                self.logger.error(f"❌ 评估个体失败: {e}")
                fitness_scores.append(-np.inf)

        return fitness_scores

    def _validate_parameters(self, params, parameter_space):
        """验证参数有效性"""
        try:
            for param_name, param_config in parameter_space.items():
                if param_name not in params:
                    return False

                param_value = params[param_name]
                param_type = param_config.get('type', 'float')
                param_range = param_config.get('range', [0, 1])

                if param_type in ['float', 'int']:
                    if param_value < param_range[0] or param_value > param_range[1]:
                        return False

                elif param_type == 'categorical':
                    if param_value not in param_config.get('categories', []):
                        return False

                elif param_type == 'bool' and not isinstance(param_value, bool):
                    return False

            return True
        except Exception as e:
            self.logger.error(f"❌ 参数验证失败: {e}")
            return False

    def _generate_new_population(self, population, fitness_scores):
        """生成新种群"""
        new_population = []

        # 转换适应度为选择概率
        fitness_scores = np.array(fitness_scores)

        # 处理负适应度
        min_fitness = np.min(fitness_scores)
        if min_fitness < 0:
            fitness_scores -= min_fitness

        # 避免除以零
        if np.sum(fitness_scores) == 0:
            selection_probs = np.ones(len(population)) / len(population)
        else:
            selection_probs = fitness_scores / np.sum(fitness_scores)

        # 生成新个体
        while len(new_population) < len(population):
            # 选择父母
            parent1_idx = np.random.choice(len(population), p=selection_probs)
            parent2_idx = np.random.choice(len(population), p=selection_probs)

            parent1 = population[parent1_idx]
            parent2 = population[parent2_idx]

            # 交叉
            if random.random() < self.crossover_rate:
                child = self._crossover(parent1, parent2)
            else:
                child = deepcopy(random.choice([parent1, parent2]))

            # 变异
            if random.random() < self.mutation_rate:
                child = self._mutate(child)

            new_population.append(child)

        return new_population

    def _crossover(self, parent1, parent2):
        """交叉操作"""
        child = {}

        for param_name in parent1.keys():
            if param_name not in parent2:
                child[param_name] = parent1[param_name]
                continue

            # 均匀交叉
            if random.random() < 0.5:
                child[param_name] = parent1[param_name]
            else:
                child[param_name] = parent2[param_name]

        return child

    def _mutate(self, individual):
        """变异操作"""
        mutated = deepcopy(individual)

        # 随机选择一个参数进行变异
        param_name = random.choice(list(mutated.keys()))
        param_value = mutated[param_name]

        if isinstance(param_value, float):
            # 高斯变异
            mutation_scale = abs(param_value) * 0.1 if param_value != 0 else 0.1
            mutated[param_name] = param_value + np.random.normal(0, mutation_scale)
        elif isinstance(param_value, int):
            # 整数变异
            mutated[param_name] = param_value + random.choice([-1, 0, 1])
        elif isinstance(param_value, bool):
            # 布尔变异
            mutated[param_name] = not param_value
        elif isinstance(param_value, str):
            # 分类变量变异（简单随机）
            mutated[param_name] = random.choice(list(individual.keys()))

        return mutated

    def _default_objective(self, backtester, params):
        """默认目标函数"""
        try:
            # 运行回测
            backtest_result = backtester.run_backtest(params)

            # 获取绩效指标
            from .performance_analyzer import PerformanceAnalyzer
            analyzer = PerformanceAnalyzer()
            performance = analyzer.analyze_performance(backtest_result)

            # 计算综合得分
            total_return = performance['return_metrics']['total_return']
            sharpe_ratio = performance['risk_adjusted_metrics']['sharpe_ratio']
            max_drawdown = performance['drawdown_metrics']['max_drawdown']

            # 目标函数: 夏普比率 * 总收益率 / 最大回撤(绝对值)
            # 避免除零
            if abs(max_drawdown) < 0.01:
                max_drawdown = 0.01

            # 计算适应度，同时考虑收益、风险和稳定性
            fitness = (sharpe_ratio * 0.4) + (total_return * 0.3) + (1 / abs(max_drawdown) * 0.3)

            return fitness

        except Exception as e:
            self.logger.error(f"❌ 计算目标函数失败: {e}")
            return -np.inf

    def bayesian_optimization(self, parameter_space, n_iter=50):
        """
        使用贝叶斯优化方法

        参数:
            parameter_space: 参数空间配置
            n_iter: 迭代次数

        返回:
            best_params: 最优参数
        """
        self.logger.info("🔧 开始贝叶斯优化")

        try:
            from skopt import gp_minimize
            from skopt.space import Real, Integer, Categorical
            from skopt.utils import use_named_args

            # 转换参数空间
            dimensions = []
            param_names = []

            for param_name, param_config in parameter_space.items():
                param_names.append(param_name)

                param_type = param_config.get('type', 'float')
                param_range = param_config.get('range', [0, 1])

                if param_type == 'float':
                    dimensions.append(Real(param_range[0], param_range[1], name=param_name))
                elif param_type == 'int':
                    dimensions.append(Integer(param_range[0], param_range[1], name=param_name))
                elif param_type == 'categorical':
                    dimensions.append(Categorical(param_config.get('categories', []), name=param_name))

            # 目标函数（需要最小化）
            @use_named_args(dimensions=dimensions)
            def objective(**params):
                # 使用默认目标函数取负数（因为贝叶斯优化是最小化）
                fitness = self._default_objective(self.backtester, params)
                return -fitness

            # 运行优化
            self.logger.info(f"📊 运行贝叶斯优化，迭代次数: {n_iter}")
            result = gp_minimize(
                objective,
                dimensions,
                n_calls=n_iter,
                random_state=42,
                verbose=True
            )

            # 转换结果
            best_params = dict(zip(param_names, result.x))
            best_fitness = -result.fun

            self.logger.info("🎉 贝叶斯优化完成")
            self.logger.info(f"   最佳适应度: {best_fitness:.4f}")
            self.logger.info(f"   最优参数: {best_params}")

            return best_params, result

        except ImportError:
            self.logger.error("❌ 无法进行贝叶斯优化，请安装 scikit-optimize")
            return None, None
        except Exception as e:
            self.logger.error(f"❌ 贝叶斯优化失败: {e}")
            return None, None

    def grid_search(self, parameter_space):
        """
        网格搜索优化方法

        参数:
            parameter_space: 参数空间配置

        返回:
            best_params: 最优参数
        """
        self.logger.info("🔧 开始网格搜索")

        # 生成参数网格
        param_grids = self._generate_grid(parameter_space)
        self.logger.info(f"   网格大小: {len(param_grids)}")

        best_fitness = -np.inf
        best_params = None

        for i, params in enumerate(param_grids):
            if i % 10 == 0:
                self.logger.info(f"📊 已搜索 {i}/{len(param_grids)} 个参数组合")

            try:
                fitness = self._default_objective(self.backtester, params)

                if fitness > best_fitness:
                    best_fitness = fitness
                    best_params = params
                    self.logger.info(f"   找到更好的参数: {best_params}, 适应度: {best_fitness:.4f}")

            except Exception as e:
                self.logger.error(f"❌ 评估参数组合失败: {e}")
                continue

        self.logger.info("🎉 网格搜索完成")
        self.logger.info(f"   最佳适应度: {best_fitness:.4f}")
        self.logger.info(f"   最优参数: {best_params}")

        return best_params

    def _generate_grid(self, parameter_space):
        """生成参数网格"""
        import itertools

        param_values = {}

        for param_name, param_config in parameter_space.items():
            param_type = param_config.get('type', 'float')
            param_range = param_config.get('range', [0, 1])

            if param_type == 'float':
                # 生成等间距浮点数
                num_points = param_config.get('grid_points', 5)
                param_values[param_name] = np.linspace(param_range[0], param_range[1], num_points)
            elif param_type == 'int':
                # 生成整数范围
                param_values[param_name] = list(range(param_range[0], param_range[1] + 1))
            elif param_type == 'categorical':
                # 使用所有分类值
                param_values[param_name] = param_config.get('categories', [])
            elif param_type == 'bool':
                # 使用布尔值
                param_values[param_name] = [True, False]

        # 生成所有组合
        keys = sorted(param_values.keys())
        combinations = itertools.product(*(param_values[key] for key in keys))

        # 转换为字典
        param_grids = [dict(zip(keys, combo)) for combo in combinations]

        return param_grids

    def generate_optimization_report(self, optimization_history):
        """生成优化报告"""
        if not optimization_history:
            return ""

        report = """
# 📈 参数优化报告

## 🎯 优化结果
"""

        best_idx = np.argmax([h['best_fitness'] for h in optimization_history])
        best_result = optimization_history[best_idx]

        report += f"""
- 最佳适应度: {best_result['best_fitness']:.4f}
- 最优参数: {best_result['best_params']}
- 找到于第 {best_result['generation']} 代

"""

        report += "## 📊 优化过程\n\n"
        report += "| 代数 | 最佳适应度 | 平均适应度 | 适应度标准差 |\n"
        report += "|------|------------|------------|--------------|\n"

        for history in optimization_history:
            report += f"| {history['generation']} | {history['best_fitness']:.4f} | {history['avg_fitness']:.4f} | {history['std_fitness']:.4f} |\n"

        return report


def main():
    """测试函数"""
    # 创建测试用的回测器
    class MockBacktester:
        def run_backtest(self, params):
            # 模拟回测结果
            return {
                'portfolio_value': pd.Series([1, 1.2, 1.1, 1.3, 1.5]),
                'transactions': pd.DataFrame({})
            }

    # 测试参数优化
    optimizer = ParameterOptimizer(MockBacktester())

    parameter_space = {
        'ma_short': {
            'type': 'int',
            'range': [5, 20]
        },
        'ma_long': {
            'type': 'int',
            'range': [20, 60]
        },
        'rsi_period': {
            'type': 'int',
            'range': [6, 14]
        },
        'rsi_overbought': {
            'type': 'float',
            'range': [70, 90]
        },
        'rsi_oversold': {
            'type': 'float',
            'range': [10, 30]
        }
    }

    best_params, history = optimizer.optimize_parameters(parameter_space)
    print("\n📋 优化报告:")
    print(optimizer.generate_optimization_report(history))


if __name__ == "__main__":
    main()