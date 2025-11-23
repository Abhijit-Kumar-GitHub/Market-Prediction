"""
GPU Memory Management Utilities

Tools for monitoring and managing GPU memory in the pipeline.
Prevents OOM errors and optimizes memory usage.
"""

import cupy as cp
import cudf
from typing import Dict, Optional
import gc


class GPUMemoryManager:
    """
    Manages GPU memory allocation and monitoring.
    
    Features:
    - Memory usage tracking
    - Automatic garbage collection
    - Memory pool management
    - OOM prevention
    """
    
    def __init__(self, limit_gb: Optional[float] = None):
        """
        Initialize GPU memory manager.
        
        Args:
            limit_gb: Memory limit in GB (None = no limit)
        """
        self.limit_gb = limit_gb
        self.mempool = cp.get_default_memory_pool()
        self.pinned_mempool = cp.get_default_pinned_memory_pool()
        
        if limit_gb:
            # Set memory limit
            self.mempool.set_limit(size=int(limit_gb * 1024**3))
    
    def get_memory_info(self) -> Dict[str, float]:
        """
        Get current GPU memory usage.
        
        Returns:
            Dictionary with memory statistics in GB
        """
        return {
            'used_gb': self.mempool.used_bytes() / 1024**3,
            'total_gb': self.mempool.total_bytes() / 1024**3,
            'free_gb': (self.mempool.total_bytes() - self.mempool.used_bytes()) / 1024**3,
            'limit_gb': self.limit_gb if self.limit_gb else float('inf'),
            'usage_pct': (self.mempool.used_bytes() / self.mempool.total_bytes() * 100) 
                         if self.mempool.total_bytes() > 0 else 0
        }
    
    def print_memory_usage(self) -> None:
        """Print formatted memory usage."""
        info = self.get_memory_info()
        print(f"GPU Memory: {info['used_gb']:.2f} / {info['total_gb']:.2f} GB "
              f"({info['usage_pct']:.1f}% used)")
        if self.limit_gb:
            print(f"  Limit: {info['limit_gb']:.2f} GB")
    
    def free_memory(self, aggressive: bool = False) -> None:
        """
        Free GPU memory.
        
        Args:
            aggressive: If True, free all cached blocks (slower next allocation)
        """
        gc.collect()  # Python garbage collection
        
        if aggressive:
            self.mempool.free_all_blocks()
            self.pinned_mempool.free_all_blocks()
        
        cp.get_default_memory_pool().free_all_blocks()
    
    def check_available(self, required_gb: float) -> bool:
        """
        Check if enough memory is available.
        
        Args:
            required_gb: Required memory in GB
        
        Returns:
            True if enough memory available
        """
        info = self.get_memory_info()
        available = info['free_gb']
        
        if self.limit_gb:
            available = min(available, self.limit_gb - info['used_gb'])
        
        return available >= required_gb
    
    def estimate_dataframe_size(self, df: cudf.DataFrame) -> float:
        """
        Estimate DataFrame memory usage in GB.
        
        Args:
            df: cuDF DataFrame
        
        Returns:
            Estimated size in GB
        """
        return df.memory_usage(deep=True).sum() / 1024**3
    
    def auto_free_if_needed(self, threshold_pct: float = 80) -> None:
        """
        Automatically free memory if usage exceeds threshold.
        
        Args:
            threshold_pct: Trigger threshold (0-100)
        """
        info = self.get_memory_info()
        if info['usage_pct'] > threshold_pct:
            print(f"⚠️  GPU memory {info['usage_pct']:.1f}% used, freeing cached blocks...")
            self.free_memory(aggressive=True)
            info = self.get_memory_info()
            print(f"   ✓ After cleanup: {info['usage_pct']:.1f}% used")


class GPUMemoryMonitor:
    """
    Context manager for monitoring GPU memory during operations.
    
    Usage:
        with GPUMemoryMonitor("Processing data"):
            # Your GPU operations here
            df = cudf.read_csv(file)
            result = df.groupby('col').mean()
    """
    
    def __init__(self, operation_name: str = "Operation"):
        """
        Initialize memory monitor.
        
        Args:
            operation_name: Name of operation being monitored
        """
        self.operation_name = operation_name
        self.manager = GPUMemoryManager()
        self.start_memory = None
    
    def __enter__(self):
        """Enter context - record starting memory."""
        self.start_memory = self.manager.get_memory_info()
        print(f"\n{'='*60}")
        print(f"🔍 Monitoring: {self.operation_name}")
        print(f"{'='*60}")
        print(f"Start memory: {self.start_memory['used_gb']:.2f} GB")
        return self.manager
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context - show memory change."""
        end_memory = self.manager.get_memory_info()
        delta = end_memory['used_gb'] - self.start_memory['used_gb']
        
        print(f"\nEnd memory:   {end_memory['used_gb']:.2f} GB")
        print(f"Delta:        {delta:+.2f} GB")
        print(f"{'='*60}\n")
        
        # Auto-cleanup if usage high
        if end_memory['usage_pct'] > 80:
            print("⚠️  High memory usage, running cleanup...")
            self.manager.free_memory(aggressive=True)


def optimize_dataframe_memory(df: cudf.DataFrame, verbose: bool = True) -> cudf.DataFrame:
    """
    Optimize DataFrame memory usage by downcasting numeric types.
    
    Args:
        df: cuDF DataFrame
        verbose: Print memory savings
    
    Returns:
        Optimized DataFrame
    """
    if verbose:
        start_mem = df.memory_usage(deep=True).sum() / 1024**2
        print(f"Memory usage before: {start_mem:.2f} MB")
    
    # Downcast integers
    for col in df.select_dtypes(include=['int64']).columns:
        df[col] = df[col].astype('int32')
    
    # Downcast floats
    for col in df.select_dtypes(include=['float64']).columns:
        df[col] = df[col].astype('float32')
    
    if verbose:
        end_mem = df.memory_usage(deep=True).sum() / 1024**2
        print(f"Memory usage after:  {end_mem:.2f} MB")
        print(f"Savings: {start_mem - end_mem:.2f} MB ({(1 - end_mem/start_mem)*100:.1f}%)")
    
    return df


def get_gpu_device_info() -> Dict:
    """
    Get GPU device information.
    
    Returns:
        Dictionary with GPU properties
    """
    device_id = cp.cuda.runtime.getDevice()
    props = cp.cuda.runtime.getDeviceProperties(device_id)
    
    return {
        'device_id': device_id,
        'name': props['name'].decode(),
        'total_memory_gb': props['totalGlobalMem'] / 1024**3,
        'compute_capability': f"{props['major']}.{props['minor']}",
        'multiprocessor_count': props['multiProcessorCount'],
        'clock_rate_mhz': props['clockRate'] / 1000,
        'memory_clock_rate_mhz': props['memoryClockRate'] / 1000
    }


def print_gpu_info():
    """Print formatted GPU device information."""
    print("=" * 60)
    print("🎮 GPU DEVICE INFORMATION")
    print("=" * 60)
    
    num_devices = cp.cuda.runtime.getDeviceCount()
    print(f"\nNumber of GPUs: {num_devices}")
    
    for i in range(num_devices):
        cp.cuda.runtime.setDevice(i)
        info = get_gpu_device_info()
        
        print(f"\n📊 GPU {i}:")
        print(f"  Name:              {info['name']}")
        print(f"  Total Memory:      {info['total_memory_gb']:.1f} GB")
        print(f"  Compute Capability: {info['compute_capability']}")
        print(f"  Multiprocessors:   {info['multiprocessor_count']}")
        print(f"  Clock Rate:        {info['clock_rate_mhz']:.0f} MHz")
    
    print("\n" + "=" * 60)


if __name__ == '__main__':
    # Test GPU memory utilities
    print("=" * 80)
    print("GPU MEMORY UTILITIES TEST")
    print("=" * 80)
    
    # Show GPU info
    print_gpu_info()
    
    # Test memory manager
    print("\n1. Testing memory manager...")
    manager = GPUMemoryManager(limit_gb=60)
    manager.print_memory_usage()
    
    # Test memory monitor
    print("\n2. Testing memory monitor...")
    with GPUMemoryMonitor("Creating test DataFrame"):
        # Create large DataFrame
        df = cudf.DataFrame({
            'a': cp.random.randn(10_000_000),
            'b': cp.random.randn(10_000_000),
            'c': cp.random.randn(10_000_000)
        })
        print(f"   Created DataFrame: {len(df):,} rows")
        
        size_gb = manager.estimate_dataframe_size(df)
        print(f"   DataFrame size: {size_gb:.2f} GB")
    
    # Test memory optimization
    print("\n3. Testing memory optimization...")
    df_int = cudf.DataFrame({'values': cp.arange(1_000_000, dtype='int64')})
    df_optimized = optimize_dataframe_memory(df_int, verbose=True)
    
    # Cleanup
    print("\n4. Testing cleanup...")
    del df, df_int, df_optimized
    manager.free_memory(aggressive=True)
    manager.print_memory_usage()
    
    print("\n" + "=" * 80)
    print("✅ TEST PASSED")
    print("=" * 80)
