# AUTOGENERATED! DO NOT EDIT! File to edit: ../00_core.ipynb.

# %% auto 0
__all__ = ['NVML']

# %% ../00_core.ipynb 2
from fastcore.utils import *
from pynvml import *
from psutil import Process
from dataclasses import dataclass

# %% ../00_core.ipynb 3
class NVML:
    "Convenient access to `pynvml` (the library behind `nvidia-smi`)"
    def __init__(self):
        nvmlInit()
        self.driver_version = nvmlSystemGetDriverVersion()
        cv = nvmlSystemGetCudaDriverVersion()
        self.cuda_version = f"{cv // 1000}.{(cv % 1000) // 10}"

    def __getitem__(self, i): return nvmlDeviceGetHandleByIndex(i)
    def __del__(self): nvmlShutdown()

# %% ../00_core.ipynb 6
@dataclass
class _Info:
    name:bytes; serial:str; uuid:bytes; persistence_mode:int; bus_id:bytes; display_active:int
    performance_state:int; fan_speed:int; temperature:int; compute_mode:int

# %% ../00_core.ipynb 7
@patch
def info(self:NVML, i:int=0) -> _Info:
    "Basic information about GPU `i`"
    h = self[i]
    return _Info(
        name=nvmlDeviceGetName(h),
        serial=nvmlDeviceGetSerial(h),
        uuid=nvmlDeviceGetUUID(h),
        persistence_mode=nvmlDeviceGetPersistenceMode(h),
        bus_id=nvmlDeviceGetPciInfo(h).busId,
        display_active=nvmlDeviceGetDisplayActive(h),
        performance_state=nvmlDeviceGetPerformanceState(h),
        fan_speed=nvmlDeviceGetFanSpeed(self[i]),
        temperature=nvmlDeviceGetTemperature(self[i], NVML_TEMPERATURE_GPU),
        compute_mode=nvmlDeviceGetComputeMode(h))

# %% ../00_core.ipynb 9
@dataclass
class _Memory: free: float; total: float; used: float

# %% ../00_core.ipynb 10
@patch
def mem(self:NVML, i:int=0)->_Memory:
    "Memory total/free/used for GPU `i`, in MB"
    res = nvmlDeviceGetMemoryInfo(self[i])
    return _Memory(*(getattr(res, fld) / 1024**2 for fld in ('free', 'total', 'used')))

# %% ../00_core.ipynb 12
@dataclass
class _Utilization: gpu: int; memory: int; enc: int; dec: int

# %% ../00_core.ipynb 13
@patch
def utilization(self:NVML, i:int=0) -> _Utilization:
    "% of time during which GPU `i` was actively using various components"
    h = self[i]
    u = nvmlDeviceGetUtilizationRates(h)
    enc, _ = nvmlDeviceGetEncoderUtilization(h)
    dec, _ = nvmlDeviceGetDecoderUtilization(h)
    return _Utilization(u.gpu, u.memory, enc, dec)

# %% ../00_core.ipynb 15
@dataclass
class _Power: usage: float; limit: float

# %% ../00_core.ipynb 16
@patch
def power(self:NVML, i:int=0) -> _Power:
    "Get power usage and limit for GPU `i` in watts"
    return _Power(
        usage=nvmlDeviceGetPowerUsage(self[i]) / 1000,
        limit=nvmlDeviceGetPowerManagementLimit(self[i]) / 1000)

# %% ../00_core.ipynb 19
@dataclass
class _Clocks: graphics: int; sm: int; mem: int

# %% ../00_core.ipynb 20
@patch
def clocks(self:NVML, i:int=0) -> _Clocks:
    "Get current clock speeds (in MHz) for GPU `i`"
    h = self[i]
    return _Clocks(
        graphics=nvmlDeviceGetClockInfo(h, NVML_CLOCK_GRAPHICS),
        sm=nvmlDeviceGetClockInfo(h, NVML_CLOCK_SM),
        mem=nvmlDeviceGetClockInfo(h, NVML_CLOCK_MEM))

# %% ../00_core.ipynb 22
@dataclass
class _PCIeThroughput: rx: float; tx: float

# %% ../00_core.ipynb 23
@patch
def pcie_throughput(self:NVML, i:int=0) -> _PCIeThroughput:
    "Get PCIe throughput (in KB/s) for GPU `i`"
    h = self[i]
    return _PCIeThroughput(
        rx=nvmlDeviceGetPcieThroughput(h, NVML_PCIE_UTIL_RX_BYTES) / 1024,
        tx=nvmlDeviceGetPcieThroughput(h, NVML_PCIE_UTIL_TX_BYTES) / 1024)

# %% ../00_core.ipynb 26
def _procinfo(p): return {'pid': p.pid, 'name': Process(p.pid).exe(), 'memory': p.usedGpuMemory / 1024**2}

# %% ../00_core.ipynb 27
@dataclass
class _ProcessInfo: pid: int; name: str; memory: float

# %% ../00_core.ipynb 28
@patch
def processes(self:NVML, i:int=0) -> List[_ProcessInfo]:
    "Get information about processes running on GPU `i`"
    h = self[i]
    procs = nvmlDeviceGetComputeRunningProcesses(h)
    return [_ProcessInfo(p.pid, Process(p.pid).exe(), p.usedGpuMemory / 1024**2) for p in procs]

# %% ../00_core.ipynb 30
@dataclass
class _DMon: pwr:float; gtemp:int; sm:int; mem:int; enc:int; dec:int; mclk:int; pclk:int

# %% ../00_core.ipynb 31
@patch
def dmon(self:NVML, i:int=0) -> _DMon:
    "Get key monitoring metrics for GPU `i`, similar to `nvidia-smi dmon`"
    power = self.power(i)
    util = self.utilization(i)
    clocks = self.clocks(i)

    return _DMon(pwr=power.usage, gtemp=self.info(i).temperature, sm=util.gpu, mem=util.memory,
        enc=util.enc, dec=util.dec, mclk=clocks.mem, pclk=clocks.graphics)
