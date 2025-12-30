# 沃尔玛PDF解析系统 - 前端开发文件

## 📁 项目结构
```
frontend/
├── src/
│   ├── components/        # 组件目录
│   │   ├── Common/       # 通用组件
│   │   └── Layout/       # 布局组件
│   ├── pages/            # 页面组件
│   ├── services/         # 服务层
│   ├── styles/           # 样式文件
│   ├── types/            # 类型定义
│   ├── App.tsx           # 应用主组件
│   └── index.tsx         # 应用入口
├── package.json          # 项目配置
└── tsconfig.json         # TypeScript配置
```

## 📦 配置文件

### 1. package.json
```json
{
  "name": "walmart-pdf-frontend",
  "version": "0.1.0",
  "private": true,
  "dependencies": {
    "@testing-library/jest-dom": "^5.17.0",
    "@testing-library/react": "^13.4.0",
    "@testing-library/user-event": "^13.5.0",
    "@types/jest": "^27.5.2",
    "@types/node": "^16.18.119",
    "@types/react": "^18.3.12",
    "@types/react-dom": "^18.3.1",
    "antd": "^6.1.1",
    "axios": "^1.13.2",
    "dayjs": "^1.11.13",
    "echarts": "^5.5.1",
    "react": "^19.2.3",
    "react-dom": "^19.2.3",
    "react-router-dom": "^7.11.0",
    "react-scripts": "5.0.1",
    "recharts": "^2.13.3",
    "typescript": "^4.9.5",
    "web-vitals": "^2.1.4",
    "zustand": "^5.0.9"
  },
  "scripts": {
    "start": "react-scripts start",
    "build": "react-scripts build",
    "test": "react-scripts test",
    "eject": "react-scripts eject"
  },
  "eslintConfig": {
    "extends": [
      "react-app",
      "react-app/jest"
    ]
  },
  "browserslist": {
    "production": [
      ">0.2%",
      "not dead",
      "not op_mini all"
    ],
    "development": [
      "last 1 chrome version",
      "last 1 firefox version",
      "last 1 safari version"
    ]
  },
  "devDependencies": {
    "@types/react-router-dom": "^5.3.3"
  }
}
```

### 2. tsconfig.json
```json
{
  "compilerOptions": {
    "target": "es5",
    "lib": [
      "dom",
      "dom.iterable",
      "esnext"
    ],
    "allowJs": true,
    "skipLibCheck": true,
    "esModuleInterop": true,
    "allowSyntheticDefaultImports": true,
    "strict": true,
    "forceConsistentCasingInFileNames": true,
    "noFallthroughCasesInSwitch": true,
    "module": "esnext",
    "moduleResolution": "node",
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "react-jsx"
  },
  "include": [
    "src"
  ]
}
```

## 📱 核心组件

### 1. MainLayout.tsx - 主布局组件
```tsx
// ============================================================
// 文件: frontend/src/components/Layout/MainLayout.tsx
// 功能: 主布局组件
// 作者: 开发团队
// 创建时间: 2025-12-20
// ============================================================

import React, { useState } from 'react';
import { Layout, Menu, Button, Dropdown, Space } from 'antd';
import {
  MenuFoldOutlined,
  MenuUnfoldOutlined,
  UserOutlined,
  FileTextOutlined,
  BarChartOutlined,
  DatabaseOutlined,
  DashboardOutlined,
} from '@ant-design/icons';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import './MainLayout.css';

const { Header, Content, Sider, Footer } = Layout;

interface MenuItem {
  key: string;
  label: React.ReactNode;
  icon: React.ReactNode;
}

const menuItems: MenuItem[] = [
  { key: '/dashboard', label: '仪表盘', icon: <DashboardOutlined /> },
  { key: '/pdfs', label: 'PDF管理', icon: <FileTextOutlined /> },
  { key: '/analytics', label: '数据分析', icon: <BarChartOutlined /> },
  { key: '/dataview', label: '数据查看', icon: <DatabaseOutlined /> },
];

const userMenu = {
  items: [
    { key: '1', label: '个人中心' },
    { key: '2', label: '设置' },
    { key: '3', label: '退出登录' },
  ],
};

interface MainLayoutProps {
  children: React.ReactNode;
}

export const MainLayout: React.FC<MainLayoutProps> = ({ children }) => {
  const [collapsed, setCollapsed] = useState(false);
  const [darkMode, setDarkMode] = useState(false);
  const location = useLocation();
  const navigate = useNavigate();

  const handleMenuClick = (e: any) => {
    navigate(e.key);
  };

  return (
    <Layout className={`main-layout ${darkMode ? 'dark-mode' : ''}`}>
      <Sider
        collapsible
        collapsed={collapsed}
        className="layout-sider"
      >
        <div className="logo">
          <Link to="/">
            <span className="logo-text">{collapsed ? '沃' : '沃尔玛PDF解析'}</span>
          </Link>
        </div>
        <Menu
          theme="dark"
          mode="inline"
          selectedKeys={[location.pathname]}
          items={menuItems}
          onClick={handleMenuClick}
        />
      </Sider>

      <Layout className="layout-main">
        <Header className="layout-header">
          <Button
            type="text"
            icon={collapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />}
            onClick={() => setCollapsed(!collapsed)}
            className="collapse-btn"
          />
          
          <div className="header-actions">
            <Button
              type="text"
              onClick={() => setDarkMode(!darkMode)}
            >
              {darkMode ? '🌞' : '🌙'}
            </Button>
            <Dropdown menu={userMenu}>
              <Button type="text" icon={<UserOutlined />}>
                用户名
              </Button>
            </Dropdown>
          </div>
        </Header>

        <Content className="layout-content">
          <div className="content-wrapper">
            {children}
          </div>
        </Content>

        <Footer className="layout-footer">
          © 2025 Walmart PDF解析系统
        </Footer>
      </Layout>
    </Layout>
  );
};
```

## 🔧 通用组件

### 1. UploadSection.tsx - 文件上传组件
```tsx
// ============================================================
// 文件: frontend/src/components/Common/UploadSection.tsx
// 功能: PDF文件上传组件
// 作者: 开发团队
// 创建时间: 2025-12-20
// ============================================================

import React, { useState } from 'react';
import { Upload, Button, message, Progress, Space } from 'antd';
import {
  UploadOutlined,
  FileTextOutlined,
  CheckCircleOutlined,
} from '@ant-design/icons';
import type { UploadProps } from 'antd';
import { PDFFile } from '../../types';
import './UploadSection.css';

interface UploadSectionProps {
  onUploadSuccess: (file: PDFFile) => void;
}

const UploadSection: React.FC<UploadSectionProps> = ({ onUploadSuccess }) => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);

  const handleFileSelect = (file: File) => {
    // 验证文件类型
    if (!file.type.includes('pdf') && !file.name.endsWith('.pdf')) {
      message.error('只能上传PDF文件');
      return false;
    }

    // 验证文件大小 (限制10MB)
    if (file.size > 10 * 1024 * 1024) {
      message.error('文件大小不能超过10MB');
      return false;
    }

    setSelectedFile(file);
    return false; // 阻止自动上传
  };

  const handleUpload = async () => {
    if (!selectedFile) {
      message.warning('请先选择文件');
      return;
    }

    setUploading(true);
    setUploadProgress(0);

    try {
      // 模拟上传进度
      const progressInterval = setInterval(() => {
        setUploadProgress((prev) => {
          const newProgress = prev + Math.random() * 30;
          return newProgress >= 90 ? 90 : newProgress;
        });
      }, 300);

      // 实际上传逻辑
      const formData = new FormData();
      formData.append('file', selectedFile);

      // 调用API上传文件
      const response = await fetch('http://localhost:8000/api/v1/pdfs/upload', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error('上传失败');
      }

      const data: PDFFile = await response.json();
      clearInterval(progressInterval);
      setUploadProgress(100);
      message.success(`文件 "${selectedFile.name}" 上传成功！`);
      onUploadSuccess(data);
    } catch (error: any) {
      message.error(`上传失败: ${error.message || '网络错误'}`);
    } finally {
      setUploading(false);
      // 重置上传状态
      setTimeout(() => {
        setUploadProgress(0);
        setSelectedFile(null);
      }, 500);
    }
  };

  const uploadProps: UploadProps = {
    beforeUpload: handleFileSelect,
    fileList: selectedFile ? [
      { uid: '1', name: selectedFile.name, size: selectedFile.size, status: 'selected' }
    ] : [],
    showUploadList: {
      showRemoveIcon: true,
      removeIcon: () => <CheckCircleOutlined />
    },
    onRemove: () => setSelectedFile(null),
  };

  return (
    <div className="upload-section">
      <Upload {...uploadProps}>
        <Button icon={<UploadOutlined />} disabled={uploading}>
          选择PDF文件
        </Button>
      </Upload>
      
      {selectedFile && (
        <div className="upload-preview">
          <div className="file-info">
            <FileTextOutlined />
            <span>{selectedFile.name}</span>
            <span className="file-size">({(selectedFile.size / 1024 / 1024).toFixed(2)} MB)</span>
          </div>
          
          {uploadProgress > 0 && (
            <Progress percent={Math.round(uploadProgress)} status={uploading ? 'active' : 'success'} />
          )}
          
          <Space>
            <Button type="primary" onClick={handleUpload} loading={uploading}>
              开始上传
            </Button>
            <Button onClick={() => setSelectedFile(null)} disabled={uploading}>
              取消
            </Button>
          </Space>
        </div>
      )}
    </div>
  );
};

export default UploadSection;
```

### 2. PDFTable.tsx - PDF列表表格组件
```tsx
// ============================================================
// 文件: frontend/src/components/Common/PDFTable.tsx
// 功能: PDF列表展示组件
// 作者: 开发团队
// 创建时间: 2025-12-20
// ============================================================

import React from 'react';
import { Table, Tag, Button, Space, Popconfirm, message } from 'antd';
import {
  EyeOutlined,
  ReloadOutlined,
  DeleteOutlined,
} from '@ant-design/icons';
import { PDFFile } from '../../types';
import './PDFTable.css';

interface StatusConfig {
  color: string;
  text: string;
}

const statusConfig: Record<string, StatusConfig> = {
  pending: { color: 'default', text: '待处理' },
  processing: { color: 'processing', text: '处理中' },
  success: { color: 'success', text: '成功' },
  failed: { color: 'error', text: '失败' },
};

interface PDFTableProps {
  data: PDFFile[];
  loading: boolean;
  onRefresh: () => void;
  onViewDetail: (record: PDFFile) => void;
  selectedRowKeys?: number[];
  onSelectChange?: (selectedRowKeys: React.Key[]) => void;
}

const PDFTable: React.FC<PDFTableProps> = ({
  data,
  loading,
  onRefresh,
  onViewDetail,
  selectedRowKeys = [],
  onSelectChange,
}) => {
  const [deleteLoading, setDeleteLoading] = useState<number | null>(null);
  const [parseLoading, setParseLoading] = useState<number | null>(null);

  const handleDelete = async (id: number, filename: string) => {
    try {
      setDeleteLoading(id);
      // 调用API删除PDF
      await fetch(`http://localhost:8000/api/v1/pdfs/${id}`, {
        method: 'DELETE',
      });
      message.success(`文件 "${filename}" 删除成功`);
      onRefresh();
    } catch (error) {
      message.error('删除失败');
    } finally {
      setDeleteLoading(null);
    }
  };

  const handleReParse = async (id: number) => {
    try {
      setParseLoading(id);
      // 调用API重新解析
      await fetch(`http://localhost:8000/api/v1/pdfs/${id}/re-parse`, {
        method: 'POST',
      });
      message.success('重新解析任务已触发');
      onRefresh();
    } catch (error) {
      message.error('重新解析失败');
    } finally {
      setParseLoading(null);
    }
  };

  const columns = [
    {
      title: '文件名',
      dataIndex: 'original_filename',
      key: 'original_filename',
      ellipsis: true,
    },
    {
      title: '文件大小',
      dataIndex: 'file_size',
      key: 'file_size',
      render: (size: number) => `${(size / 1024 / 1024).toFixed(2)} MB`,
    },
    {
      title: '上传时间',
      dataIndex: 'upload_time',
      key: 'upload_time',
      render: (time: string) => new Date(time).toLocaleString(),
    },
    {
      title: '处理状态',
      dataIndex: 'process_status',
      key: 'process_status',
      render: (status: string) => (
        <Tag color={statusConfig[status]?.color || 'default'}>
          {statusConfig[status]?.text || status}
        </Tag>
      ),
    },
    {
      title: '操作',
      key: 'action',
      render: (_, record: PDFFile) => (
        <Space size="middle">
          <Button
            icon={<EyeOutlined />}
            onClick={() => onViewDetail(record)}
            disabled={record.process_status !== 'success'}
          >
            查看
          </Button>
          <Button
            icon={<ReloadOutlined />}
            onClick={() => handleReParse(record.id)}
            loading={parseLoading === record.id}
          >
            重新解析
          </Button>
          <Popconfirm
            title="确定要删除这个文件吗？"
            onConfirm={() => handleDelete(record.id, record.original_filename)}
          >
            <Button
              danger
              icon={<DeleteOutlined />}
              loading={deleteLoading === record.id}
            >
              删除
            </Button>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  const rowSelection = {
    selectedRowKeys,
    onChange: onSelectChange,
  };

  return (
    <div className="pdf-table">
      <Table
        rowKey="id"
        dataSource={data}
        columns={columns}
        loading={loading}
        rowSelection={rowSelection}
        pagination={{
          pageSize: 10,
          showSizeChanger: true,
          showTotal: (total) => `共 ${total} 条记录`,
        }}
        bordered
      />
    </div>
  );
};

export default PDFTable;
```

## 📄 页面组件

### 1. PDFManagement/index.tsx - PDF管理页面
```tsx
// ============================================================
// 文件: frontend/src/pages/PDFManagement/index.tsx
// 功能: PDF文件管理页面
// 作者: 开发团队
// 创建时间: 2025-12-20
// ============================================================

import React, { useState, useEffect } from 'react';
import { Card, Row, Col, Statistic, Button, Space, message } from 'antd';
import { ReloadOutlined } from '@ant-design/icons';
import { PDFFile } from '../../types';
import UploadSection from '../../components/Common/UploadSection';
import PDFTable from '../../components/Common/PDFTable';
import './PDFManagement.css';

interface Statistics {
  total: number;
  success: number;
  processing: number;
  failed: number;
}

const PDFManagement: React.FC = () => {
  const [pdfList, setPdfList] = useState<PDFFile[]>([]);
  const [loading, setLoading] = useState(false);
  const [selectedRowKeys, setSelectedRowKeys] = useState<number[]>([]);
  const [statistics, setStatistics] = useState<Statistics>({
    total: 0,
    success: 0,
    processing: 0,
    failed: 0,
  });

  const fetchPDFList = async () => {
    try {
      setLoading(true);
      const response = await fetch('http://localhost:8000/api/v1/pdfs/');
      if (!response.ok) {
        throw new Error('获取数据失败');
      }
      const data = await response.json();
      setPdfList(data.items || []);
      
      // 计算统计数据
      const stats = {
        total: data.total || 0,
        success: data.items.filter((item: PDFFile) => item.process_status === 'success').length,
        processing: data.items.filter((item: PDFFile) => item.process_status === 'processing').length,
        failed: data.items.filter((item: PDFFile) => item.process_status === 'failed').length,
      };
      setStatistics(stats);
    } catch (error: any) {
      message.error(`获取PDF列表失败: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPDFList();
  }, []);

  const handleViewDetail = (record: PDFFile) => {
    // 跳转到详情页
    window.location.href = `/statements/${record.id}`;
  };

  const handleDeleteAll = async () => {
    if (selectedRowKeys.length === 0) {
      message.warning('请先选择要删除的文件');
      return;
    }

    try {
      setLoading(true);
      // 调用批量删除API
      await fetch('http://localhost:8000/api/v1/pdfs/batch-delete', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ ids: selectedRowKeys }),
      });
      message.success(`成功删除 ${selectedRowKeys.length} 个文件`);
      fetchPDFList();
      setSelectedRowKeys([]);
    } catch (error) {
      message.error('批量删除失败');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="pdf-management">
      <h2>📁 PDF文件管理</h2>
      
      <Card className="upload-card">
        <UploadSection onUploadSuccess={() => fetchPDFList()} />
      </Card>

      <Card className="statistics-card">
        <Row gutter={16}>
          <Col xs={24} sm={6}>
            <Statistic title="总文件数" value={statistics.total} prefix="📊" />
          </Col>
          <Col xs={24} sm={6}>
            <Statistic title="成功处理" value={statistics.success} prefix="✅" />
          </Col>
          <Col xs={24} sm={6}>
            <Statistic title="处理中" value={statistics.processing} prefix="⏳" />
          </Col>
          <Col xs={24} sm={6}>
            <Statistic title="处理失败" value={statistics.failed} prefix="❌" />
          </Col>
        </Row>
      </Card>

      <Card 
        title="PDF文件列表" 
        extra={
          <Space>
            <Button icon={<ReloadOutlined />} onClick={fetchPDFList} loading={loading}>
              刷新
            </Button>
            {selectedRowKeys.length > 0 && (
              <Button danger onClick={handleDeleteAll}>
                批量删除 ({selectedRowKeys.length})
              </Button>
            )}
          </Space>
        }
      >
        <PDFTable
          data={pdfList}
          loading={loading}
          onRefresh={fetchPDFList}
          onViewDetail={handleViewDetail}
          selectedRowKeys={selectedRowKeys}
          onSelectChange={(keys) => setSelectedRowKeys(keys as number[])}
        />
      </Card>
    </div>
  );
};

export default PDFManagement;
```

### 2. Analytics/index.tsx - 数据分析页面
```tsx
// ============================================================
// 文件: frontend/src/pages/Analytics/index.tsx
// 功能: 数据分析页面
// 作者: 开发团队
// 创建时间: 2025-12-20
// ============================================================

import React, { useState } from 'react';
import { Card, Tabs, DatePicker, Button, Space, Select, Divider } from 'antd';
import { ExportOutlined, FilterOutlined } from '@ant-design/icons';
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import dayjs from 'dayjs';
import './Analytics.css';

const { RangePicker } = DatePicker;
const { TabPane } = Tabs;
const { Option } = Select;

// 模拟数据
const mockTrendData = [
  { period: '12/1', 销售额: 12000, 退款: 2000, 净收入: 10000 },
  { period: '12/2', 销售额: 15000, 退款: 1500, 净收入: 13500 },
  { period: '12/3', 销售额: 18000, 退款: 2500, 净收入: 15500 },
  { period: '12/4', 销售额: 14000, 退款: 1800, 净收入: 12200 },
  { period: '12/5', 销售额: 20000, 退款: 2200, 净收入: 17800 },
  { period: '12/6', 销售额: 22000, 退款: 2000, 净收入: 20000 },
  { period: '12/7', 销售额: 19000, 退款: 1500, 净收入: 17500 },
];

const mockComparisonData = {
  period1: { 销售额: 80000, 退款: 12000, 净收入: 68000, 订单数: 1200 },
  period2: { 销售额: 95000, 退款: 13500, 净收入: 81500, 订单数: 1450 },
  changes: {
    销售额: { absolute: 15000, percentage: 18.75 },
    退款: { absolute: 1500, percentage: 12.5 },
    净收入: { absolute: 13500, percentage: 19.85 },
    订单数: { absolute: 250, percentage: 20.83 },
  },
};

const mockAnomalyData = [
  { id: 1, period: '12/5', type: '高退款率', metric: '退款', value: 2200, threshold: 1500, severity: 'high' },
  { id: 2, period: '12/3', type: '低销售额', metric: '销售额', value: 18000, threshold: 25000, severity: 'medium' },
  { id: 3, period: '12/6', type: '异常订单', metric: '订单数', value: 1450, threshold: 1200, severity: 'low' },
];

const Analytics: React.FC = () => {
  const [dateRange, setDateRange] = useState<[dayjs.Dayjs, dayjs.Dayjs] | null>([
    dayjs().subtract(7, 'day'),
    dayjs(),
  ]);
  const [granularity, setGranularity] = useState('day');

  const handleExport = (format: string) => {
    // 导出功能实现
    console.log(`Exporting data to ${format}`);
  };

  const TrendTab = () => (
    <ResponsiveContainer width="100%" height={400}>
      <LineChart data={mockTrendData}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="period" />
        <YAxis />
        <Tooltip formatter={(value) => [`¥${value}`, '金额']} />
        <Legend />
        <Line type="monotone" dataKey="销售额" stroke="#52c41a" activeDot={{ r: 8 }} />
        <Line type="monotone" dataKey="退款" stroke="#f5222d" />
        <Line type="monotone" dataKey="净收入" stroke="#722ed1" />
      </LineChart>
    </ResponsiveContainer>
  );

  const ComparisonTab = () => (
    <ResponsiveContainer width="100%" height={400}>
      <BarChart data={[
        { name: '销售额', 期间1: mockComparisonData.period1.销售额, 期间2: mockComparisonData.period2.销售额 },
        { name: '退款', 期间1: mockComparisonData.period1.退款, 期间2: mockComparisonData.period2.退款 },
        { name: '净收入', 期间1: mockComparisonData.period1.净收入, 期间2: mockComparisonData.period2.净收入 },
        { name: '订单数', 期间1: mockComparisonData.period1.订单数, 期间2: mockComparisonData.period2.订单数 },
      ]}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="name" />
        <YAxis />
        <Tooltip formatter={(value) => [`¥${value}`, '金额']} />
        <Legend />
        <Bar dataKey="期间1" fill="#1890ff" />
        <Bar dataKey="期间2" fill="#52c41a" />
      </BarChart>
    </ResponsiveContainer>
  );

  return (
    <div className="analytics-page">
      <h2>📊 数据分析</h2>
      
      <Card className="filter-card">
        <Space direction="vertical" size="middle" style={{ width: '100%' }}>
          <Row justify="space-between" align="middle">
            <Space>
              <RangePicker 
                value={dateRange}
                onChange={setDateRange}
                style={{ width: 300 }}
              />
              <Select 
                value={granularity}
                onChange={setGranularity}
                style={{ width: 120 }}
              >
                <Option value="day">按天</Option>
                <Option value="week">按周</Option>
                <Option value="month">按月</Option>
              </Select>
              <Button icon={<FilterOutlined />} type="primary">
                应用筛选
              </Button>
            </Space>
            <Dropdown menu={{ 
              items: [
                { key: '1', label: '导出Excel', onClick: () => handleExport('excel') },
                { key: '2', label: '导出CSV', onClick: () => handleExport('csv') },
              ]
            }}>
              <Button icon={<ExportOutlined />}>导出数据</Button>
            </Dropdown>
          </Row>
        </Space>
      </Card>

      <Tabs defaultActiveKey="trend" className="analytics-tabs">
        <TabPane tab="趋势分析" key="trend">
          <Card>
            <TrendTab />
          </Card>
        </TabPane>
        <TabPane tab="对比分析" key="comparison">
          <Card>
            <ComparisonTab />
          </Card>
        </TabPane>
        <TabPane tab="异常检测" key="anomaly">
          <Card>
            {/* 异常检测内容 */}
            <div className="anomaly-list">
              {mockAnomalyData.map((item) => (
                <div key={item.id} className={`anomaly-item severity-${item.severity}`}>
                  <div className="anomaly-info">
                    <span className="period">{item.period}</span>
                    <span className="type">{item.type}</span>
                    <span className="metric">{item.metric}: ¥{item.value}</span>
                  </div>
                  <div className="anomaly-severity">
                    {item.severity === 'high' && <span className="high">高</span>}
                    {item.severity === 'medium' && <span className="medium">中</span>}
                    {item.severity === 'low' && <span className="low">低</span>}
                  </div>
                </div>
              ))}
            </div>
          </Card>
        </TabPane>
      </Tabs>
    </div>
  );
};

export default Analytics;
```

### 3. DataView/index.tsx - 数据查看页面
```tsx
// ============================================================
// 文件: frontend/src/pages/DataView/index.tsx
// 功能: 对账单数据查看页面
// 作者: 开发团队
// 创建时间: 2025-12-20
// ============================================================

import React, { useState, useEffect } from 'react';
import { Card, Tabs, Button, Space, message, Form, Input, Row, Col, Statistic } from 'antd';
import { ExportOutlined, SaveOutlined } from '@ant-design/icons';
import { useParams } from 'react-router-dom';
import { CompleteStatementData } from '../../types';
import './DataView.css';

const { TabPane } = Tabs;
const { TextArea } = Input;

// 模拟数据
const mockStatementData: CompleteStatementData = {
  pdf_file: {
    id: 1,
    filename: 'sample.pdf',
    original_filename: 'Walmart_Statement_202512.pdf',
    file_size: 2048000,
    file_hash: 'abc123',
    upload_time: '2025-12-20T10:30:00',
    process_status: 'success',
    process_time: '2025-12-20T10:35:00',
    created_at: '2025-12-20T10:30:00',
    updated_at: '2025-12-20T10:35:00',
  },
  statement_header: {
    id: 1,
    pdf_file_id: 1,
    start_date: '2025-11-01',
    end_date: '2025-11-30',
    opening_balance: 50000,
    reserve_funds: 10000,
    awaiting_payment: 5000,
  },
  sales_detail: {
    id: 1,
    pdf_file_id: 1,
    product_price: 80000,
    shipping: 5000,
    wfs_shipping_refund: 1000,
    net_tax_collected: 8000,
    net_commission: -12000,
    withholding_tax: -1500,
    wfs_shipping_tax_refund: 200,
    walmart_funded_savings: -500,
    total: 78200,
    other_total: 0,
  },
  refund_detail: {
    id: 1,
    pdf_file_id: 1,
    product_price: -12000,
    shipping: -800,
    net_tax_collected: -1200,
    commission: 1800,
    withholding_tax: 180,
    walmart_funded_savings: 60,
    total: -12060,
    other_total: 0,
  },
  adjustment_detail: {
    id: 1,
    pdf_file_id: 1,
    global_shipping_label_fee: -500,
    other_total: 0,
  },
  wfs_detail: {
    id: 1,
    pdf_file_id: 1,
    wfs_fee: -3000,
    wfs_ethereum_fee: -200,
    wfs_total_discount: -100,
    total: -3300,
    other_total: 0,
  },
  other_activity_detail: {
    id: 1,
    pdf_file_id: 1,
    walmart_product_ads: -2000,
    total: -2000,
    other_total: 0,
  },
  statement_footer: {
    id: 1,
    pdf_file_id: 1,
    amount_paid_to_you: 100000,
    closing_balance: 150000,
    other_total: 0,
  },
  payment_detail: {
    id: 1,
    pdf_file_id: 1,
    status: 'paid',
    payment_date: '2025-12-05',
    payment_frequency: 'weekly',
    payment_method: 'bank_transfer',
    device_method: 'online',
    amount_to_be_paid: 100000,
    amount_waiting_return: 0,
    return_waiting_period: '',
    warning_message: '',
  },
};

const StatementHeaderForm: React.FC<{ form: any; isEditing: boolean }> = ({ form, isEditing }) => {
  return (
    <Row gutter={16}>
      <Col span={8}>
        <Form.Item label="开始日期" name="start_date">
          <Input disabled={!isEditing} />
        </Form.Item>
      </Col>
      <Col span={8}>
        <Form.Item label="结束日期" name="end_date">
          <Input disabled={!isEditing} />
        </Form.Item>
      </Col>
      <Col span={8}>
        <Form.Item label="期初余额" name="opening_balance">
          <Input type="number" disabled={!isEditing} />
        </Form.Item>
      </Col>
      <Col span={8}>
        <Form.Item label="预留资金" name="reserve_funds">
          <Input type="number" disabled={!isEditing} />
        </Form.Item>
      </Col>
      <Col span={8}>
        <Form.Item label="待付款项" name="awaiting_payment">
          <Input type="number" disabled={!isEditing} />
        </Form.Item>
      </Col>
    </Row>
  );
};

const SalesDetailForm: React.FC<{ form: any; isEditing: boolean }> = ({ form, isEditing }) => {
  return (
    <Row gutter={16}>
      <Col span={8}>
        <Form.Item label="产品价格" name="product_price">
          <Input type="number" disabled={!isEditing} />
        </Form.Item>
      </Col>
      <Col span={8}>
        <Form.Item label="运费" name="shipping">
          <Input type="number" disabled={!isEditing} />
        </Form.Item>
      </Col>
      <Col span={8}>
        <Form.Item label="净税收" name="net_tax_collected">
          <Input type="number" disabled={!isEditing} />
        </Form.Item>
      </Col>
      <Col span={8}>
        <Form.Item label="净佣金" name="net_commission">
          <Input type="number" disabled={!isEditing} />
        </Form.Item>
      </Col>
      <Col span={8}>
        <Form.Item label="销售总额" name="total">
          <Input type="number" disabled={!isEditing} />
        </Form.Item>
      </Col>
    </Row>
  );
};

const DataView: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const [form] = Form.useForm();
  const [isEditing, setIsEditing] = useState(false);
  const [saving, setSaving] = useState(false);
  const [statementData, setStatementData] = useState<CompleteStatementData | null>(null);

  useEffect(() => {
    // 模拟API调用获取数据
    setStatementData(mockStatementData);
    form.setFieldsValue({
      ...mockStatementData.statement_header,
      ...mockStatementData.sales_detail,
      ...mockStatementData.refund_detail,
      ...mockStatementData.adjustment_detail,
      ...mockStatementData.wfs_detail,
      ...mockStatementData.other_activity_detail,
      ...mockStatementData.statement_footer,
      ...mockStatementData.payment_detail,
    });
  }, [id, form]);

  const handleSave = async () => {
    try {
      setSaving(true);
      const values = await form.validateFields();
      // 调用API保存数据
      console.log('Saving data:', values);
      message.success('保存成功');
      setIsEditing(false);
    } catch (error) {
      message.error('保存失败');
    } finally {
      setSaving(false);
    }
  };

  const handleExport = (format: string) => {
    // 导出功能实现
    console.log(`Exporting statement data to ${format}`);
  };

  if (!statementData) {
    return <div>加载中...</div>;
  }

  return (
    <div className="data-view-page">
      <h2>📋 对账单详情</h2>
      
      <Card className="summary-card">
        <Row gutter={16}>
          <Col xs={24} sm={6}>
            <Statistic title="期间" value={`${new Date(statementData.statement_header.start_date).toLocaleDateString()} - ${new Date(statementData.statement_header.end_date).toLocaleDateString()}`} />
          </Col>
          <Col xs={24} sm={6}>
            <Statistic title="销售总额" value={statementData.sales_detail.total} prefix="¥" />
          </Col>
          <Col xs={24} sm={6}>
            <Statistic title="退款总额" value={statementData.refund_detail.total} prefix="¥" />
          </Col>
          <Col xs={24} sm={6}>
            <Statistic title="应付金额" value={statementData.statement_footer.amount_paid_to_you} prefix="¥" />
          </Col>
        </Row>
      </Card>

      <Card 
        extra={
          <Space>
            <Dropdown menu={{ 
              items: [
                { key: '1', label: '导出Excel', onClick: () => handleExport('excel') },
                { key: '2', label: '导出PDF', onClick: () => handleExport('pdf') },
                { key: '3', label: '导出CSV', onClick: () => handleExport('csv') },
              ]
            }}>
              <Button icon={<ExportOutlined />}>导出</Button>
            </Dropdown>
            {!isEditing ? (
              <Button type="primary" onClick={() => setIsEditing(true)}>
                编辑
              </Button>
            ) : (
              <Space>
                <Button onClick={() => setIsEditing(false)}>
                  取消
                </Button>
                <Button type="primary" icon={<SaveOutlined />} onClick={handleSave} loading={saving}>
                  保存
                </Button>
              </Space>
            )}
          </Space>
        }
      >
        <Form form={form} layout="vertical">
          <Tabs defaultActiveKey="header">
            <TabPane tab="📋 对账单头部" key="header">
              <StatementHeaderForm form={form} isEditing={isEditing} />
            </TabPane>
            <TabPane tab="💰 销售明细" key="sales">
              <SalesDetailForm form={form} isEditing={isEditing} />
            </TabPane>
            <TabPane tab="🔄 退款明细" key="refund">
              {/* 退款明细表单 */}
              <div>退款明细表单内容</div>
            </TabPane>
            <TabPane tab="⚙️ 调整明细" key="adjustment">
              {/* 调整明细表单 */}
              <div>调整明细表单内容</div>
            </TabPane>
            <TabPane tab="📦 WFS明细" key="wfs">
              {/* WFS明细表单 */}
              <div>WFS明细表单内容</div>
            </TabPane>
            <TabPane tab="📊 其他活动" key="other">
              {/* 其他活动表单 */}
              <div>其他活动表单内容</div>
            </TabPane>
            <TabPane tab="📄 对账单尾部" key="footer">
              {/* 对账单尾部表单 */}
              <div>对账单尾部表单内容</div>
            </TabPane>
            <TabPane tab="💸 付款详情" key="payment">
              {/* 付款详情表单 */}
              <div>付款详情表单内容</div>
            </TabPane>
          </Tabs>
        </Form>
      </Card>
    </div>
  );
};

export default DataView;
```

## 📡 服务层

### 1. api.ts - API基础配置
```tsx
// ============================================================
// 文件: frontend/src/services/api.ts
// 功能: Axios实例和拦截器配置
// 作者: 开发团队
// 创建时间: 2025-12-20
// ============================================================

import axios, { AxiosInstance, AxiosError } from 'axios';

// API基础URL
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

// 创建Axios实例
const apiClient: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// 请求拦截器
apiClient.interceptors.request.use(
  (config) => {
    // 可以在这里添加token等认证信息
    const token = localStorage.getItem('authToken');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// 响应拦截器
apiClient.interceptors.response.use(
  (response) => {
    return response;
  },
  (error: AxiosError) => {
    // 统一错误处理
    if (error.response) {
      // 服务器响应了错误状态码
      const status = error.response.status;
      if (status === 401) {
        // 未授权，清除token并重定向
        localStorage.removeItem('authToken');
        window.location.href = '/login';
      } else if (status === 403) {
        console.error('禁止访问: ', error.response.data);
      } else if (status === 404) {
        console.error('资源不存在: ', error.response.data);
      } else if (status === 500) {
        console.error('服务器错误: ', error.response.data);
      }
    } else if (error.request) {
      // 请求已发出，但没有收到响应
      console.error('网络错误: 无响应');
    } else {
      // 请求配置出错
      console.error('错误: ', error.message);
    }
    return Promise.reject(error);
  }
);

export default apiClient;
```

### 2. pdfService.ts - PDF服务
```tsx
// ============================================================
// 文件: frontend/src/services/pdfService.ts
// 功能: PDF相关API服务
// 作者: 开发团队
// 创建时间: 2025-12-20
// ============================================================

import apiClient from './api';
import { PDFFile, PDFListResponse } from '../types';

// PDF管理API服务
export const pdfService = {
  // 上传PDF文件
  uploadPDF: async (file: File): Promise<PDFFile> => {
    const formData = new FormData();
    formData.append('file', file);

    const response = await apiClient.post<PDFFile>(
      '/api/v1/pdfs/upload',
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      }
    );
    return response.data;
  },

  // 获取PDF列表
  getPDFList: async (page: number = 1, pageSize: number = 10): Promise<PDFListResponse> => {
    const response = await apiClient.get<PDFListResponse>('/api/v1/pdfs/', {
      params: { page, page_size: pageSize },
    });
    return response.data;
  },

  // 获取PDF详情
  getPDFDetail: async (pdfId: number): Promise<PDFFile> => {
    const response = await apiClient.get<PDFFile>(`/api/v1/pdfs/${pdfId}`);
    return response.data;
  },

  // 删除PDF
  deletePDF: async (pdfId: number): Promise<{ message: string }> => {
    const response = await apiClient.delete(`/api/v1/pdfs/${pdfId}`);
    return response.data;
  },

  // 重新触发解析
  reParsePDF: async (pdfId: number): Promise<PDFFile> => {
    const response = await apiClient.post<PDFFile>(`/api/v1/pdfs/${pdfId}/re-parse`);
    return response.data;
  },
};

export default pdfService;
```

## 📝 类型定义

### types/index.ts - 全局类型定义
```tsx
// ============================================================
// 文件: frontend/src/types/index.ts
// 功能: 全局TypeScript类型定义
// 作者: 开发团队
// 创建时间: 2025-12-20
// ============================================================

// ========== PDF相关类型 ==========
export interface PDFFile {
  id: number;
  filename: string;
  original_filename: string;
  file_size: number;
  file_hash: string;
  upload_time: string;
  process_status: 'pending' | 'processing' | 'success' | 'failed';
  process_time?: string;
  error_message?: string;
  created_at: string;
  updated_at: string;
}

export interface PDFListResponse {
  total: number;
  page: number;
  page_size: number;
  items: PDFFile[];
}

// ========== 对账单数据类型 ==========
export interface StatementHeader {
  id: number;
  pdf_file_id: number;
  start_date: string;
  end_date: string;
  opening_balance?: number;
  reserve_funds?: number;
  awaiting_payment?: number;
}

export interface SalesDetail {
  id: number;
  pdf_file_id: number;
  product_price?: number;
  shipping?: number;
  wfs_shipping_refund?: number;
  net_tax_collected?: number;
  net_commission?: number;
  withholding_tax?: number;
  wfs_shipping_tax_refund?: number;
  walmart_funded_savings?: number;
  total?: number;
  other_total?: number;
}

export interface RefundDetail {
  id: number;
  pdf_file_id: number;
  product_price?: number;
  shipping?: number;
  net_tax_collected?: number;
  commission?: number;
  withholding_tax?: number;
  walmart_funded_savings?: number;
  total?: number;
  other_total?: number;
}

export interface AdjustmentDetail {
  id: number;
  pdf_file_id: number;
  global_shipping_label_fee?: number;
  other_total?: number;
}

export interface WFSDetail {
  id: number;
  pdf_file_id: number;
  wfs_fee?: number;
  wfs_ethereum_fee?: number;
  wfs_total_discount?: number;
  total?: number;
  other_total?: number;
}

export interface OtherActivityDetail {
  id: number;
  pdf_file_id: number;
  walmart_product_ads?: number;
  total?: number;
  other_total?: number;
}

export interface StatementFooter {
  id: number;
  pdf_file_id: number;
  amount_paid_to_you?: number;
  closing_balance?: number;
  other_total?: number;
}

export interface PaymentDetail {
  id: number;
  pdf_file_id: number;
  status?: string;
  payment_date?: string;
  payment_frequency?: string;
  payment_method?: string;
  device_method?: string;
  amount_to_be_paid?: number;
  amount_waiting_return?: number;
  return_waiting_period?: string;
  warning_message?: string;
}

export interface CompleteStatementData {
  pdf_file: PDFFile;
  statement_header: StatementHeader;
  sales_detail: SalesDetail;
  refund_detail: RefundDetail;
  adjustment_detail: AdjustmentDetail;
  wfs_detail: WFSDetail;
  other_activity_detail: OtherActivityDetail;
  statement_footer: StatementFooter;
  payment_detail: PaymentDetail;
}

// ========== 数据分析类型 ==========
export interface AggregatedMetrics {
  total_sales: number;
  total_refund: number;
  total_commission: number;
  total_wfs_fee: number;
  total_ads_cost: number;
  net_revenue: number;
  statement_count: number;
  period_days: number;
}

export interface PeriodData {
  period_label: string;
  start_date: string;
  end_date: string;
  metrics: AggregatedMetrics;
}

export interface TrendAnalysisResponse {
  time_series: PeriodData[];
  granularity: string;
  total_periods: number;
}

export interface ComparisonResponse {
  period1: AggregatedMetrics;
  period2: AggregatedMetrics;
  changes: {
    [key: string]: {
      absolute: number;
      percentage: number;
    };
  };
}

export interface AnomalyItem {
  pdf_id: number;
  statement_period: string;
  anomaly_type: string;
  metric_name: string;
  metric_value: number;
  threshold: number;
  severity: 'low' | 'medium' | 'high';
  message: string;
}

export interface AnomalyDetectionResponse {
  total_statements: number;
  anomaly_count: number;
  anomalies: AnomalyItem[];
}

// ========== API响应类型 ==========
export interface ApiResponse<T> {
  code: number;
  message: string;
  data: T;
}

export interface ApiErrorResponse {
  detail: string;
}

// ========== 应用状态类型 ==========
export interface AppState {
  currentPDFId?: number;
  isLoading: boolean;
  error?: string;
  selectedDateRange?: [string, string];
}
```

## 🚀 应用入口

### 1. App.tsx - 应用主组件
```tsx
// ============================================================
// 文件: frontend/src/App.tsx
// 功能: 主应用组件和路由配置
// 作者: 开发团队
// 创建时间: 2025-12-20
// ============================================================

import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { ConfigProvider } from 'antd';
import zhCN from 'antd/locale/zh_CN';
import { MainLayout } from './components/Layout';
import PDFManagement from './pages/PDFManagement';
import DataView from './pages/DataView';
import Analytics from './pages/Analytics';
import './styles/index.css';

// 临时占位符组件
const Dashboard = () => (
  <div>
    <h2>📊 仪表盘</h2>
    <p>Dashboard - 建设中</p>
  </div>
);

const App: React.FC = () => {
  return (
    <ConfigProvider locale={zhCN}>
      <Router>
        <MainLayout>
          <Routes>
            {/* 重定向首页到Dashboard */}
            <Route path="/" element={<Navigate to="/dashboard" replace />} />

            {/* 主要页面路由 */}
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/pdfs" element={<PDFManagement />} />
            <Route path="/statements/:id" element={<DataView />} />
            <Route path="/analytics" element={<Analytics />} />

            {/* 404页面 */}
            <Route path="*" element={<Navigate to="/dashboard" replace />} />
          </Routes>
        </MainLayout>
      </Router>
    </ConfigProvider>
  );
};

export default App;
```

### 2. index.tsx - 应用入口
```tsx
// ============================================================
// 文件: frontend/src/index.tsx
// 功能: 应用入口文件
// 作者: 开发团队
// 创建时间: 2025-12-20
// ============================================================

import React from 'react';
import ReactDOM from 'react-dom/client';
import './index.css';
import App from './App';
import reportWebVitals from './reportWebVitals';

const root = ReactDOM.createRoot(
  document.getElementById('root') as HTMLElement
);
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);

// If you want to start measuring performance in your app, pass a function
// to log results (for example: reportWebVitals(console.log))
// or send to an analytics endpoint. Learn more: https://bit.ly/CRA-vitals
reportWebVitals();
```

## 📖 开发说明

### 技术栈
- **框架**: React 19 + TypeScript
- **UI组件库**: Ant Design 6
- **状态管理**: Zustand
- **路由**: React Router 7
- **HTTP客户端**: Axios
- **数据可视化**: Recharts + ECharts
- **日期处理**: dayjs

### 开发流程
1. **启动开发服务器**: `npm start`
2. **构建生产版本**: `npm run build`
3. **运行测试**: `npm test`
4. **代码检查**: `npm run lint`

### API接口
- **基础URL**: http://localhost:8000
- **文档地址**: http://localhost:8000/api/docs

### 组件开发规范
1. **文件命名**: 使用 PascalCase
2. **组件命名**: 与文件名保持一致
3. **类型定义**: 使用 TypeScript 接口定义组件props
4. **注释**: 关键逻辑添加注释
5. **样式**: 使用 CSS Modules

---

📅 更新时间: 2025-12-23 14:30
