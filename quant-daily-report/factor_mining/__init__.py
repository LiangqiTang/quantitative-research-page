"""
因子挖掘模块
提供基于RD-Agent的因子挖掘、分析和回测功能
"""

# 使用延迟导入，避免依赖缺失导致模块无法导入
__all__ = [
    'RDAgentFactorMiner',
    'FactorMiningEngine',
    'get_factor_miner'
]

# 保持向后兼容性
__version__ = '1.0.0'
__author__ = 'Quant Research Team'

# 延迟导入实现
_rd_agent_factor_miner = None
_factor_mining_engine = None


def __getattr__(name):
    global _rd_agent_factor_miner, _factor_mining_engine

    if name == 'RDAgentFactorMiner':
        if _rd_agent_factor_miner is None:
            try:
                from .rd_agent_factor_miner import RDAgentFactorMiner
                _rd_agent_factor_miner = RDAgentFactorMiner
            except ImportError as e:
                raise ImportError(
                    "无法导入RDAgentFactorMiner，请先安装RD-Agent依赖:\n"
                    "pip install rdagent\n"
                    "或者访问: https://github.com/your-org/rdagent 获取安装说明"
                ) from e
        return _rd_agent_factor_miner

    elif name == 'FactorMiningEngine':
        if _factor_mining_engine is None:
            try:
                from .factor_mining_engine import FactorMiningEngine
                _factor_mining_engine = FactorMiningEngine
            except ImportError as e:
                raise ImportError(
                    "无法导入FactorMiningEngine，请先安装依赖:\n"
                    "pip install pandas numpy scikit-learn"
                ) from e
        return _factor_mining_engine

    elif name == 'get_factor_miner':
        return get_factor_miner

    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")


def get_factor_miner(miner_type: str = 'builtin'):
    """
    获取因子挖掘器实例
    :param miner_type: 挖掘器类型，目前支持 'builtin' 和 'rdagent'
    :return: 因子挖掘器实例
    """
    try:
        if miner_type == 'builtin':
            from .built_in_factor_miner import BuiltInFactorMiner
            return BuiltInFactorMiner()
        elif miner_type == 'rdagent':
            from .rd_agent_factor_miner import RDAgentFactorMiner
            return RDAgentFactorMiner()
        else:
            raise ValueError(f"不支持的因子挖掘器类型: {miner_type}")
    except Exception as e:
        raise RuntimeError(f"创建因子挖掘器失败: {e}") from e
