import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import sqlite3
from datetime import datetime

class InventorySystem:
    def __init__(self, root):
        """初始化进销存管理系统"""
        self.root = root
        self.root.title("进销存管理系统")
        self.root.geometry("1200x800")  # 增加窗口大小以适应更多内容
        
        # 设置账套列表
        self.account_sets = ["账套1", "账套2", "账套3"]
        
        # 创建账套选择下拉菜单
        self.init_account_set_selector()
        
        # 设置默认账套
        self.current_db_file = "账套1.db"
        
        # 创建数据库连接
        self.init_database()
        
        # 创建主框架
        self.main_frame = ttk.Frame(root)
        self.main_frame.pack(expand=True, fill='both', padx=10, pady=5)
        
        # 创建标签页
        self.notebook = ttk.Notebook(self.main_frame)
        self.notebook.pack(expand=True, fill='both')
        
        # 创建各个功能页面
        self.inventory_frame = ttk.Frame(self.notebook)
        self.transactions_frame = ttk.Frame(self.notebook)
        self.customers_frame = ttk.Frame(self.notebook)
        self.suppliers_frame = ttk.Frame(self.notebook)  # 新增供应商页面
        self.orders_frame = ttk.Frame(self.notebook)
        
        # 添加标签页
        self.notebook.add(self.inventory_frame, text="库存管理")
        self.notebook.add(self.transactions_frame, text="资金往来")
        self.notebook.add(self.customers_frame, text="客户管理")
        self.notebook.add(self.suppliers_frame, text="供应商管理")
        self.notebook.add(self.orders_frame, text="订单管理")
        
        # 初始化各个页面
        self.init_inventory_page()
        self.init_transactions_page()
        self.init_customers_page()
        self.init_suppliers_page()
        self.init_orders_page()
        
        # 初始化所有下拉列表数据
        self.refresh_all_combos()

        #刷新一下所有界面
        self.refresh_all()

    def init_database(self):
        """初始化数据库结构"""
        if self.current_db_file is None:
            messagebox.showerror("错误", "请选择一个账套")
            return
                
        self.conn = sqlite3.connect(self.current_db_file)
        self.cursor = self.conn.cursor()
        
        # 创建商品分类表
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE
            )
        ''')
        
        # 创建供应商表
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS suppliers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                contact TEXT,
                address TEXT,
                notes TEXT,
                type TEXT NOT NULL
            )
        ''')
        
        # 创建库存表
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS inventory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                category_id INTEGER,
                quantity INTEGER NOT NULL,
                purchase_price REAL NOT NULL,  -- 进货价
                selling_price REAL NOT NULL,   -- 销售价
                supplier_id INTEGER,
                warning_level INTEGER DEFAULT 10,
                FOREIGN KEY (category_id) REFERENCES categories (id),
                FOREIGN KEY (supplier_id) REFERENCES suppliers (id)
            )
        ''')
        
        # 创建客户表
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS customers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                contact TEXT,
                address TEXT,
                notes TEXT,
                type TEXT NOT NULL  -- 客户类型：意向客户/已合作客户/已联系客户
            )
        ''')
        
        # 创建订单表
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_id INTEGER NOT NULL,
                date TEXT NOT NULL,
                business_type TEXT NOT NULL,  -- 对公/对私
                total_amount REAL NOT NULL,   -- 订单总金额
                freight_cost REAL DEFAULT 0,  -- 运费
                commission REAL DEFAULT 0,    -- 回扣
                notes TEXT,                   -- 备注
                FOREIGN KEY (customer_id) REFERENCES customers (id)
            )
        ''')
        
        # 创建订单明细表
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS order_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                quantity INTEGER NOT NULL,
                price REAL NOT NULL,
                FOREIGN KEY (order_id) REFERENCES orders (id),
                FOREIGN KEY (product_id) REFERENCES inventory (id)
            )
        ''')
        
        # 创建资金往来表
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                type TEXT NOT NULL,           -- 收入/支出
                business_type TEXT NOT NULL,   -- 对公/对私
                amount REAL NOT NULL,
                description TEXT,
                customer_id INTEGER,
                supplier_id INTEGER,
                order_id INTEGER,
                FOREIGN KEY (customer_id) REFERENCES customers (id),
                FOREIGN KEY (supplier_id) REFERENCES suppliers (id),
                FOREIGN KEY (order_id) REFERENCES orders (id)
            )
        ''')
        
        # 提交事务
        self.conn.commit()

    def init_inventory_page(self):
        """初始化库存管理页面"""
        # 创建左侧分类树形结构
        category_frame = ttk.Frame(self.inventory_frame)
        category_frame.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=5)
        
        ttk.Label(category_frame, text="商品分类").pack(pady=5)
        
        self.category_tree = ttk.Treeview(category_frame, columns=('id', 'name'), show='headings', height=20)
        self.category_tree.heading('id', text='ID')
        self.category_tree.heading('name', text='分类名称')
        # 设置列宽
        self.category_tree.column('id', width=50)  # 设置 ID 列的宽度为 50 像素
        self.category_tree.column('name', width=150)  # 设置 分类名称 列的宽度为 150 像素
        self.category_tree.pack(fill=tk.Y, expand=True)
        
        # 分类管理按钮
        category_btn_frame = ttk.Frame(category_frame)
        category_btn_frame.pack(pady=5)
        ttk.Button(category_btn_frame, text="添加分类", command=self.add_category).pack(side=tk.LEFT, padx=2)
        ttk.Button(category_btn_frame, text="删除分类", command=self.delete_category).pack(side=tk.LEFT, padx=2)
        
        # 创建右侧商品列表
        product_frame = ttk.Frame(self.inventory_frame)
        product_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 商品列表
        self.inventory_tree = ttk.Treeview(
            product_frame,
            columns=('ID', '名称', '分类', '数量', '进货价', '销售价', '供应商', '预警值'),
            show='headings',
            height=20
        )
        
        # 设置列标题
        self.inventory_tree.heading('ID', text='ID')
        self.inventory_tree.heading('名称', text='名称')
        self.inventory_tree.heading('分类', text='分类')
        self.inventory_tree.heading('数量', text='数量')
        self.inventory_tree.heading('进货价', text='进货价')
        self.inventory_tree.heading('销售价', text='销售价')
        self.inventory_tree.heading('供应商', text='供应商')
        self.inventory_tree.heading('预警值', text='预警值')
        
        # 设置列宽
        for col in self.inventory_tree['columns']:
            self.inventory_tree.column(col, width=100)
        
        self.inventory_tree.pack(fill=tk.BOTH, expand=True)
        
        # 添加商品输入框
        input_frame = ttk.LabelFrame(product_frame, text="商品信息")
        input_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # 第一行
        row1 = ttk.Frame(input_frame)
        row1.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(row1, text='商品名称:').pack(side=tk.LEFT, padx=5)
        self.name_var = tk.StringVar()
        ttk.Entry(row1, textvariable=self.name_var).pack(side=tk.LEFT, padx=5)
        
        ttk.Label(row1, text='分类:').pack(side=tk.LEFT, padx=5)
        self.category_var = tk.StringVar()
        self.category_combo = ttk.Combobox(row1, textvariable=self.category_var, state='readonly')
        self.category_combo.pack(side=tk.LEFT, padx=5)
        
        ttk.Label(row1, text='供应商:').pack(side=tk.LEFT, padx=5)
        self.supplier_var = tk.StringVar()
        self.supplier_combo = ttk.Combobox(row1, textvariable=self.supplier_var, state='readonly')
        self.supplier_combo.pack(side=tk.LEFT, padx=5)
        
        # 第二行
        row2 = ttk.Frame(input_frame)
        row2.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(row2, text='数量:').pack(side=tk.LEFT, padx=5)
        self.quantity_var = tk.StringVar()
        ttk.Entry(row2, textvariable=self.quantity_var).pack(side=tk.LEFT, padx=5)
        
        ttk.Label(row2, text='进货价:').pack(side=tk.LEFT, padx=5)
        self.purchase_price_var = tk.StringVar()
        ttk.Entry(row2, textvariable=self.purchase_price_var).pack(side=tk.LEFT, padx=5)
        
        ttk.Label(row2, text='销售价:').pack(side=tk.LEFT, padx=5)
        self.selling_price_var = tk.StringVar()
        ttk.Entry(row2, textvariable=self.selling_price_var).pack(side=tk.LEFT, padx=5)
        
        ttk.Label(row2, text='预警值:').pack(side=tk.LEFT, padx=5)
        self.warning_level_var = tk.StringVar(value='10')
        ttk.Entry(row2, textvariable=self.warning_level_var).pack(side=tk.LEFT, padx=5)
        
        # 按钮行
        btn_frame = ttk.Frame(input_frame)
        btn_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(btn_frame, text='添加商品', command=self.add_inventory).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text='编辑商品', command=self.edit_inventory).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text='删除商品', command=self.delete_inventory).pack(side=tk.LEFT, padx=5)
        
        # 添加右键菜单
        self.inventory_menu = tk.Menu(self.inventory_tree, tearoff=0)
        self.inventory_menu.add_command(label="编辑", command=self.edit_inventory)
        self.inventory_menu.add_command(label="删除", command=self.delete_inventory)
        
        # 绑定右键事件
        self.inventory_tree.bind("<Button-3>", self.show_inventory_menu)
        
        # 绑定选择事件
        self.category_tree.bind('<<TreeviewSelect>>', self.on_category_select)

    def init_transactions_page(self):
        """初始化资金往来页面"""
        # 创建主框架
        main_frame = ttk.Frame(self.transactions_frame)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 创建交易记录列表
        self.transactions_tree = ttk.Treeview(
            main_frame,
            columns=('ID', '日期', '类型', '业务类型', '金额', '客户/供应商', '关联订单', '描述'),
            show='headings',
            height=20
        )
        
        # 设置列标题
        self.transactions_tree.heading('ID', text='ID')
        self.transactions_tree.heading('日期', text='日期')
        self.transactions_tree.heading('类型', text='类型')
        self.transactions_tree.heading('业务类型', text='业务类型')
        self.transactions_tree.heading('金额', text='金额')
        self.transactions_tree.heading('客户/供应商', text='客户/供应商')
        self.transactions_tree.heading('关联订单', text='关联订单')
        self.transactions_tree.heading('描述', text='描述')
        
        # 设置列宽
        for col in self.transactions_tree['columns']:
            self.transactions_tree.column(col, width=100)
        self.transactions_tree.column('描述', width=200)
        
        self.transactions_tree.pack(fill=tk.BOTH, expand=True)
        
        # 创建输入框架
        input_frame = ttk.LabelFrame(main_frame, text="交易信息")
        input_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # 第一行
        row1 = ttk.Frame(input_frame)
        row1.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(row1, text='交易类型:').pack(side=tk.LEFT, padx=5)
        self.trans_type_var = tk.StringVar()
        ttk.Combobox(
            row1,
            textvariable=self.trans_type_var,
            values=['收入', '支出'],
            state='readonly'
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Label(row1, text='业务类型:').pack(side=tk.LEFT, padx=5)
        self.business_type_var = tk.StringVar()
        ttk.Combobox(
            row1,
            textvariable=self.business_type_var,
            values=['对公', '对私'],
            state='readonly'
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Label(row1, text='金额:').pack(side=tk.LEFT, padx=5)
        self.amount_var = tk.StringVar()
        ttk.Entry(row1, textvariable=self.amount_var).pack(side=tk.LEFT, padx=5)
        
        # 第二行
        row2 = ttk.Frame(input_frame)
        row2.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(row2, text='客户:').pack(side=tk.LEFT, padx=5)
        self.trans_customer_var = tk.StringVar()
        self.trans_customer_combo = ttk.Combobox(
            row2,
            textvariable=self.trans_customer_var,
            state='readonly'
        )
        self.trans_customer_combo.pack(side=tk.LEFT, padx=5)
        
        ttk.Label(row2, text='供应商:').pack(side=tk.LEFT, padx=5)
        self.trans_supplier_var = tk.StringVar()
        self.trans_supplier_combo = ttk.Combobox(
            row2,
            textvariable=self.trans_supplier_var,
            state='readonly'
        )
        self.trans_supplier_combo.pack(side=tk.LEFT, padx=5)
        
        ttk.Label(row2, text='关联订单:').pack(side=tk.LEFT, padx=5)
        self.trans_order_var = tk.StringVar()
        self.trans_order_combo = ttk.Combobox(
            row2,
            textvariable=self.trans_order_var,
            state='readonly'
        )
        self.trans_order_combo.pack(side=tk.LEFT, padx=5)
        
        # 第三行
        row3 = ttk.Frame(input_frame)
        row3.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(row3, text='描述:').pack(side=tk.LEFT, padx=5)
        self.description_var = tk.StringVar()
        ttk.Entry(row3, textvariable=self.description_var, width=50).pack(side=tk.LEFT, padx=5)
        
        # 按钮行
        btn_frame = ttk.Frame(input_frame)
        btn_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(btn_frame, text='添加交易', command=self.add_transaction).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text='编辑交易', command=self.edit_transaction).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text='删除交易', command=self.delete_transaction).pack(side=tk.LEFT, padx=5)
        
        # 添加右键菜单
        self.transactions_menu = tk.Menu(self.transactions_tree, tearoff=0)
        self.transactions_menu.add_command(label="编辑", command=self.edit_transaction)
        self.transactions_menu.add_command(label="删除", command=self.delete_transaction)
        
        # 绑定右键事件
        self.transactions_tree.bind("<Button-3>", self.show_transactions_menu)

    def init_customers_page(self):
        """初始化客户管理页面"""
        # 创建主框架
        main_frame = ttk.Frame(self.customers_frame)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 创建客户列表
        self.customers_tree = ttk.Treeview(
            main_frame,
            columns=('ID', '名称', '联系方式', '地址', '备注', '类型'),
            show='headings',
            height=20
        )
        
        # 设置列标题
        self.customers_tree.heading('ID', text='ID')
        self.customers_tree.heading('名称', text='名称')
        self.customers_tree.heading('联系方式', text='联系方式')
        self.customers_tree.heading('地址', text='地址')
        self.customers_tree.heading('备注', text='备注')
        self.customers_tree.heading('类型', text='类型')
        
        # 设置列宽
        for col in self.customers_tree['columns']:
            self.customers_tree.column(col, width=100)
        self.customers_tree.column('地址', width=200)
        self.customers_tree.column('备注', width=200)
        
        self.customers_tree.pack(fill=tk.BOTH, expand=True)
        
        # 创建输入框架
        input_frame = ttk.LabelFrame(main_frame, text="客户信息")
        input_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # 第一行
        row1 = ttk.Frame(input_frame)
        row1.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(row1, text='客户名称:').pack(side=tk.LEFT, padx=5)
        self.customer_name_var = tk.StringVar()
        ttk.Entry(row1, textvariable=self.customer_name_var).pack(side=tk.LEFT, padx=5)
        
        ttk.Label(row1, text='联系方式:').pack(side=tk.LEFT, padx=5)
        self.contact_var = tk.StringVar()
        ttk.Entry(row1, textvariable=self.contact_var).pack(side=tk.LEFT, padx=5)
        
        ttk.Label(row1, text='客户类型:').pack(side=tk.LEFT, padx=5)
        self.customer_type_var = tk.StringVar()
        ttk.Combobox(
            row1,
            textvariable=self.customer_type_var,
            values=['意向客户', '已合作客户', '已联系客户'],
            state='readonly'
        ).pack(side=tk.LEFT, padx=5)
        
        # 第二行
        row2 = ttk.Frame(input_frame)
        row2.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(row2, text='地址:').pack(side=tk.LEFT, padx=5)
        self.address_var = tk.StringVar()
        ttk.Entry(row2, textvariable=self.address_var, width=50).pack(side=tk.LEFT, padx=5)
        
        # 第三行
        row3 = ttk.Frame(input_frame)
        row3.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(row3, text='备注:').pack(side=tk.LEFT, padx=5)
        self.notes_var = tk.StringVar()
        ttk.Entry(row3, textvariable=self.notes_var, width=50).pack(side=tk.LEFT, padx=5)
        
        # 按钮行
        btn_frame = ttk.Frame(input_frame)
        btn_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(btn_frame, text='添加客户', command=self.add_customer).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text='编辑客户', command=self.edit_customer).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text='删除客户', command=self.delete_customer).pack(side=tk.LEFT, padx=5)
        
        # 添加右键菜单
        self.customers_menu = tk.Menu(self.customers_tree, tearoff=0)
        self.customers_menu.add_command(label="编辑", command=self.edit_customer)
        self.customers_menu.add_command(label="删除", command=self.delete_customer)
        
        # 绑定右键事件
        self.customers_tree.bind("<Button-3>", self.show_customers_menu)

    def init_suppliers_page(self):
        """初始化供应商管理页面"""
        # 创建主框架
        main_frame = ttk.Frame(self.suppliers_frame)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 创建供应商列表
        self.suppliers_tree = ttk.Treeview(
            main_frame,
            columns=('ID', '名称', '联系方式', '地址', '备注', '类型'),
            show='headings',
            height=20
        )
        
        # 设置列标题
        self.suppliers_tree.heading('ID', text='ID')
        self.suppliers_tree.heading('名称', text='名称')
        self.suppliers_tree.heading('联系方式', text='联系方式')
        self.suppliers_tree.heading('地址', text='地址')
        self.suppliers_tree.heading('备注', text='备注')
        self.suppliers_tree.heading('类型', text='类型')
        
        # 设置列宽
        for col in self.suppliers_tree['columns']:
            self.suppliers_tree.column(col, width=100)
        self.suppliers_tree.column('地址', width=200)
        self.suppliers_tree.column('备注', width=200)
        
        self.suppliers_tree.pack(fill=tk.BOTH, expand=True)
        
        # 创建输入框架
        input_frame = ttk.LabelFrame(main_frame, text="供应商信息")
        input_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # 第一行
        row1 = ttk.Frame(input_frame)
        row1.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(row1, text='供应商名称:').pack(side=tk.LEFT, padx=5)
        self.supplier_name_var = tk.StringVar()
        ttk.Entry(row1, textvariable=self.supplier_name_var).pack(side=tk.LEFT, padx=5)
        
        ttk.Label(row1, text='联系方式:').pack(side=tk.LEFT, padx=5)
        self.supplier_contact_var = tk.StringVar()
        ttk.Entry(row1, textvariable=self.supplier_contact_var).pack(side=tk.LEFT, padx=5)
        
        ttk.Label(row1, text='供应商类型:').pack(side=tk.LEFT, padx=5)
        self.supplier_type_var = tk.StringVar()
        ttk.Combobox(
            row1,
            textvariable=self.supplier_type_var,
            values=['生产商', '代理商', '批发商'],
            state='readonly'
        ).pack(side=tk.LEFT, padx=5)
        
        # 第二行
        row2 = ttk.Frame(input_frame)
        row2.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(row2, text='地址:').pack(side=tk.LEFT, padx=5)
        self.supplier_address_var = tk.StringVar()
        ttk.Entry(row2, textvariable=self.supplier_address_var, width=50).pack(side=tk.LEFT, padx=5)
        
        # 第三行
        row3 = ttk.Frame(input_frame)
        row3.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(row3, text='备注:').pack(side=tk.LEFT, padx=5)
        self.supplier_notes_var = tk.StringVar()
        ttk.Entry(row3, textvariable=self.supplier_notes_var, width=50).pack(side=tk.LEFT, padx=5)
        
        # 按钮行
        btn_frame = ttk.Frame(input_frame)
        btn_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(btn_frame, text='添加供应商', command=self.add_supplier).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text='编辑供应商', command=self.edit_supplier).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text='删除供应商', command=self.delete_supplier).pack(side=tk.LEFT, padx=5)
        
        # 添加右键菜单
        self.suppliers_menu = tk.Menu(self.suppliers_tree, tearoff=0)
        self.suppliers_menu.add_command(label="编辑", command=self.edit_supplier)
        self.suppliers_menu.add_command(label="删除", command=self.delete_supplier)
        
        # 绑定右键事件
        self.suppliers_tree.bind("<Button-3>", self.show_suppliers_menu)

    def init_orders_page(self):
        """初始化订单管理页面"""
        # 创建主框架
        main_frame = ttk.Frame(self.orders_frame)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 创建订单列表
        self.orders_tree = ttk.Treeview(
            main_frame,
            columns=('ID', '客户', '日期', '业务类型', '总金额', '运费', '回扣', '备注'),
            show='headings',
            height=15
        )
        
        # 设置列标题
        self.orders_tree.heading('ID', text='ID')
        self.orders_tree.heading('客户', text='客户')
        self.orders_tree.heading('日期', text='日期')
        self.orders_tree.heading('业务类型', text='业务类型')
        self.orders_tree.heading('总金额', text='总金额')
        self.orders_tree.heading('运费', text='运费')
        self.orders_tree.heading('回扣', text='回扣')
        self.orders_tree.heading('备注', text='备注')
        
        # 设置列宽
        for col in self.orders_tree['columns']:
            self.orders_tree.column(col, width=100)
        self.orders_tree.column('备注', width=200)
        
        self.orders_tree.pack(fill=tk.BOTH, expand=True)
        
        # 创建订单明细列表
        detail_frame = ttk.LabelFrame(main_frame, text="订单明细")
        detail_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 创建订单明细列表
        self.order_items_tree = ttk.Treeview(
            detail_frame,
            columns=('ID', '商品名称', '数量', '单价', '小计'),
            show='headings',
            height=5
        )
        
        # 设置列标题
        self.order_items_tree.heading('ID', text='ID')
        self.order_items_tree.heading('商品名称', text='商品名称')
        self.order_items_tree.heading('数量', text='数量')
        self.order_items_tree.heading('单价', text='单价')
        self.order_items_tree.heading('小计', text='小计')
        
        # 设置列宽
        for col in self.order_items_tree['columns']:
            self.order_items_tree.column(col, width=100)
        
        self.order_items_tree.pack(fill=tk.BOTH, expand=True)
        
        # 创建输入框架
        input_frame = ttk.LabelFrame(main_frame, text="订单信息")
        input_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # 第一行
        row1 = ttk.Frame(input_frame)
        row1.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(row1, text='客户:').pack(side=tk.LEFT, padx=5)
        self.order_customer_var = tk.StringVar()
        self.order_customer_combo = ttk.Combobox(
            row1,
            textvariable=self.order_customer_var,
            state='readonly'
        )
        self.order_customer_combo.pack(side=tk.LEFT, padx=5)
        
        ttk.Label(row1, text='业务类型:').pack(side=tk.LEFT, padx=5)
        self.order_business_type_var = tk.StringVar()
        ttk.Combobox(
            row1,
            textvariable=self.order_business_type_var,
            values=['对公', '对私'],
            state='readonly'
        ).pack(side=tk.LEFT, padx=5)
        
        # 第二行
        row2 = ttk.Frame(input_frame)
        row2.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(row2, text='运费:').pack(side=tk.LEFT, padx=5)
        self.freight_cost_var = tk.StringVar(value='0.0')
        ttk.Entry(row2, textvariable=self.freight_cost_var).pack(side=tk.LEFT, padx=5)
        
        ttk.Label(row2, text='回扣:').pack(side=tk.LEFT, padx=5)
        self.commission_var = tk.StringVar(value='0.0')
        ttk.Entry(row2, textvariable=self.commission_var).pack(side=tk.LEFT, padx=5)
        
        # 第三行
        row3 = ttk.Frame(input_frame)
        row3.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(row3, text='备注:').pack(side=tk.LEFT, padx=5)
        self.order_notes_var = tk.StringVar()
        ttk.Entry(row3, textvariable=self.order_notes_var, width=50).pack(side=tk.LEFT, padx=5)
        
        # 第四行（新增收款方式）
        row4 = ttk.Frame(input_frame)
        row4.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(row4, text='收款方式:').pack(side=tk.LEFT, padx=5)
        self.payment_method_var = tk.StringVar()
        ttk.Combobox(
            row4,
            textvariable=self.payment_method_var,
            values=['公户', '支付宝', '微信', '私人银行卡'],
            state='readonly'
        ).pack(side=tk.LEFT, padx=5)
        
        # 商品选择框架
        product_frame = ttk.LabelFrame(input_frame, text="添加商品")
        product_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # 第一行
        p_row1 = ttk.Frame(product_frame)
        p_row1.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(p_row1, text='商品:').pack(side=tk.LEFT, padx=5)
        self.order_product_var = tk.StringVar()
        self.order_product_combo = ttk.Combobox(
            p_row1,
            textvariable=self.order_product_var,
            values=self.order_product_combo['values'],
            state='readonly'
        )
        self.order_product_combo.pack(side=tk.LEFT, padx=5)
        
        ttk.Label(p_row1, text='数量:').pack(side=tk.LEFT, padx=5)
        self.order_quantity_var = tk.StringVar(value='1')
        ttk.Entry(p_row1, textvariable=self.order_quantity_var).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(p_row1, text='添加商品', command=self.add_order_item).pack(side=tk.LEFT, padx=5)
        ttk.Button(p_row1, text='删除商品', command=self.delete_order_item).pack(side=tk.LEFT, padx=5)
        
        # 按钮行
        btn_frame = ttk.Frame(input_frame)
        btn_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(btn_frame, text='保存订单', command=self.save_order).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text='编辑订单', command=self.edit_order).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text='删除订单', command=self.delete_order).pack(side=tk.LEFT, padx=5)
        
        # 添加右键菜单
        self.orders_menu = tk.Menu(self.orders_tree, tearoff=0)
        self.orders_menu.add_command(label="编辑", command=self.edit_order)
        self.orders_menu.add_command(label="删除", command=self.delete_order)
        
        # 绑定右键事件
        self.orders_tree.bind("<Button-3>", self.show_orders_menu)


    def refresh_all_combos(self):
        """刷新所有下拉列表的数据"""
        self.update_customer_combos()
        self.update_supplier_combos()
        self.update_product_combos()
        self.update_category_combos()
        self.update_order_combo()

    def update_customer_combos(self):
        """更新所有客户下拉列表"""
        self.cursor.execute('SELECT id, name FROM customers')
        customers = self.cursor.fetchall()
        customer_list = [f"{id} - {name}" for id, name in customers]
        
        self.order_customer_combo['values'] = customer_list
        self.trans_customer_combo['values'] = customer_list

    def update_supplier_combos(self):
        """更新所有供应商下拉列表"""
        self.cursor.execute('SELECT id, name FROM suppliers')
        suppliers = self.cursor.fetchall()
        supplier_list = [f"{id} - {name}" for id, name in suppliers]
        
        self.supplier_combo['values'] = supplier_list
        self.trans_supplier_combo['values'] = supplier_list

    def update_product_combos(self):
        """更新所有商品下拉列表"""
        self.cursor.execute('SELECT id, name, selling_price FROM inventory')
        products = self.cursor.fetchall()
        product_list = [f"{id} - {name} (¥{price})" for id, name, price in products]
        
        self.order_product_combo['values'] = product_list

    def update_category_combos(self):
        """更新所有分类下拉列表"""
        self.cursor.execute('SELECT id, name FROM categories')
        categories = self.cursor.fetchall()
        category_list = [f"{id} - {name}" for id, name in categories]
        
        self.category_combo['values'] = category_list

    def update_order_combo(self):
        """更新订单下拉列表"""
        self.cursor.execute('''
            SELECT o.id, c.name, o.total_amount 
            FROM orders o 
            JOIN customers c ON o.customer_id = c.id
        ''')
        orders = self.cursor.fetchall()
        order_list = [f"{id} - {name} (¥{amount})" for id, name, amount in orders]
        
        self.trans_order_combo['values'] = order_list

    def show_inventory_menu(self, event):
        """显示库存右键菜单"""
        item = self.inventory_tree.identify_row(event.y)
        if item:
            self.inventory_tree.selection_set(item)
            self.inventory_menu.post(event.x_root, event.y_root)

    def show_transactions_menu(self, event):
        """显示交易记录右键菜单"""
        item = self.transactions_tree.identify_row(event.y)
        if item:
            self.transactions_tree.selection_set(item)
            self.transactions_menu.post(event.x_root, event.y_root)

    def show_customers_menu(self, event):
        """显示客户右键菜单"""
        item = self.customers_tree.identify_row(event.y)
        if item:
            self.customers_tree.selection_set(item)
            self.customers_menu.post(event.x_root, event.y_root)

    def show_suppliers_menu(self, event):
        """显示供应商右键菜单"""
        item = self.suppliers_tree.identify_row(event.y)
        if item:
            self.suppliers_tree.selection_set(item)
            self.suppliers_menu.post(event.x_root, event.y_root)

    def show_orders_menu(self, event):
        """显示订单右键菜单"""
        item = self.orders_tree.identify_row(event.y)
        if item:
            self.orders_tree.selection_set(item)
            self.orders_menu.post(event.x_root, event.y_root)

    def add_category(self):
        """添加商品分类"""
        name = simpledialog.askstring("添加分类", "请输入分类名称:")
        if name:
            try:
                self.cursor.execute('INSERT INTO categories (name) VALUES (?)', (name,))
                self.conn.commit()
                self.refresh_categories()
                self.update_category_combos()
                messagebox.showinfo('成功', '分类添加成功')
            except sqlite3.IntegrityError:
                messagebox.showerror('错误', '该分类名称已存在')
            except sqlite3.Error as e:
                messagebox.showerror('错误', f'添加分类失败: {e}')

    def delete_category(self):
        """删除商品分类"""
        selected = self.category_tree.selection()
        if not selected:
            messagebox.showwarning('警告', '请选择要删除的分类')
            return
            
        category_id = self.category_tree.item(selected)['values'][0]
        
        # 检查是否有商品使用此分类
        self.cursor.execute('SELECT COUNT(*) FROM inventory WHERE category_id = ?', (category_id,))
        if self.cursor.fetchone()[0] > 0:
            messagebox.showerror('错误', '该分类下有商品，无法删除')
            return
            
        if messagebox.askyesno('确认', '确定要删除该分类吗？'):
            try:
                self.cursor.execute('DELETE FROM categories WHERE id = ?', (category_id,))
                self.conn.commit()
                self.refresh_categories()
                self.update_category_combos()
                messagebox.showinfo('成功', '分类删除成功')
            except sqlite3.Error as e:
                messagebox.showerror('错误', f'删除分类失败: {e}')

    def refresh_categories(self):
        """刷新分类列表"""
        for item in self.category_tree.get_children():
            self.category_tree.delete(item)
            
        self.cursor.execute('SELECT * FROM categories')
        for row in self.cursor.fetchall():
            self.category_tree.insert('', 'end', values=row)

    def on_category_select(self, event):
        """分类选择事件处理"""
        selected = self.category_tree.selection()
        if selected:
            category_id = self.category_tree.item(selected)['values'][0]
            self.refresh_inventory_by_category(category_id)

    def refresh_inventory_by_category(self, category_id):
        """根据分类刷新商品列表"""
        for item in self.inventory_tree.get_children():
            self.inventory_tree.delete(item)
            
        self.cursor.execute('''
            SELECT i.*, c.name as category_name, s.name as supplier_name
            FROM inventory i
            LEFT JOIN categories c ON i.category_id = c.id
            LEFT JOIN suppliers s ON i.supplier_id = s.id
            WHERE i.category_id = ?
        ''', (category_id,))
        
        for row in self.cursor.fetchall():
            self.inventory_tree.insert('', 'end', values=row)

#商品库存模块开始=======================================================

    def refresh_inventory(self):
        """刷新库存列表"""
        # 清空当前列表
        for i in self.inventory_tree.get_children():
            self.inventory_tree.delete(i)
        
        # 查询最新数据
        self.cursor.execute('SELECT * FROM inventory')
        rows = self.cursor.fetchall()
        
        # 插入新数据
        for row in rows:
            self.inventory_tree.insert("", "end", values=row)
    
    def update_product_combos(self):
        """更新产品组合框"""
        # 更新产品组合框的代码
        pass
    
    def clear_inventory_inputs(self):
        """清空输入框"""
        self.name_var.set('')
        self.category_var.set('')
        self.supplier_var.set('')
        self.quantity_var.set('')
        self.purchase_price_var.set('')
        self.selling_price_var.set('')
        self.warning_level_var.set('')

    def add_inventory(self):
        """添加库存商品"""
        try:
            # 获取输入值
            name = self.name_var.get()
            category = self.category_var.get().split(' - ')[0] if self.category_var.get() else None
            supplier = self.supplier_var.get().split(' - ')[0] if self.supplier_var.get() else None
            quantity = int(self.quantity_var.get() or 0)
            purchase_price = float(self.purchase_price_var.get() or 0)
            selling_price = float(self.selling_price_var.get() or 0)
            warning_level = int(self.warning_level_var.get() or 0)
            
            # 验证必填项
            if not name or not category:
                messagebox.showerror('错误', '商品名称和分类为必填项')
                return
                
            # 验证数值(验证添加商品时，数量、价格和预警值不能为负数，暂时注释掉)
            #if quantity <= 0 or purchase_price <= 0 or selling_price <= 0 or warning_level <= 0:
            #    messagebox.showerror('错误', '数量、价格和预警值不能为负数')
            #    return
                
            # 插入数据
            self.cursor.execute('''
                INSERT INTO inventory (
                    name, category_id, supplier_id, quantity,
                    purchase_price, selling_price, warning_level
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (name, category, supplier, quantity, purchase_price, selling_price, warning_level))
            
            self.conn.commit()
            self.refresh_inventory()
            self.update_product_combos()
            self.clear_inventory_inputs()
            messagebox.showinfo('成功', '商品添加成功')
            
        except ValueError:
            messagebox.showerror('错误', '请输入有效的数字')
        except sqlite3.Error as e:
            messagebox.showerror('错误', f'添加商品失败: {e}')

    def edit_inventory(self):
        """编辑库存商品"""
        selected = self.inventory_tree.selection()
        if not selected:
            messagebox.showwarning('警告', '请选择要编辑的商品')
            return
            
        item_id = self.inventory_tree.item(selected)['values'][0]
        
        # 获取商品信息
        self.cursor.execute('''
            SELECT i.*, c.name as category_name, s.name as supplier_name
            FROM inventory i
            LEFT JOIN categories c ON i.category_id = c.id
            LEFT JOIN suppliers s ON i.supplier_id = s.id
            WHERE i.id = ?
        ''', (item_id,))
        
        item = self.cursor.fetchone()
        if not item:
            messagebox.showerror('错误', '商品不存在')
            return
            
        # 创建编辑窗口
        edit_window = tk.Toplevel(self.root)
        edit_window.title("编辑商品信息")
        edit_window.geometry("500x400")
        
        # 创建输入框架
        input_frame = ttk.LabelFrame(edit_window, text="商品信息")
        input_frame.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
        
        # 商品名称
        ttk.Label(input_frame, text="商品名称:").grid(row=0, column=0, padx=5, pady=5)
        name_var = tk.StringVar(value=item[1])
        ttk.Entry(input_frame, textvariable=name_var).grid(row=0, column=1, padx=5, pady=5)
        
        # 分类
        ttk.Label(input_frame, text="分类:").grid(row=1, column=0, padx=5, pady=5)
        category_var = tk.StringVar(value=f"{item[2]} - {item[-2]}" if item[2] else "")
        category_combo = ttk.Combobox(input_frame, textvariable=category_var, state='readonly')
        category_combo['values'] = self.category_combo['values']
        category_combo.grid(row=1, column=1, padx=5, pady=5)
        
        # 供应商
        ttk.Label(input_frame, text="供应商:").grid(row=2, column=0, padx=5, pady=5)
        supplier_var = tk.StringVar(value=f"{item[6]} - {item[-1]}" if item[6] else "")
        supplier_combo = ttk.Combobox(input_frame, textvariable=supplier_var, state='readonly')
        supplier_combo['values'] = self.supplier_combo['values']
        supplier_combo.grid(row=2, column=1, padx=5, pady=5)
        
        # 数量
        ttk.Label(input_frame, text="数量:").grid(row=3, column=0, padx=5, pady=5)
        quantity_var = tk.StringVar(value=item[3])
        ttk.Entry(input_frame, textvariable=quantity_var).grid(row=3, column=1, padx=5, pady=5)
        
        # 进货价
        ttk.Label(input_frame, text="进货价:").grid(row=4, column=0, padx=5, pady=5)
        purchase_price_var = tk.StringVar(value=item[4])
        ttk.Entry(input_frame, textvariable=purchase_price_var).grid(row=4, column=1, padx=5, pady=5)
        
        # 销售价
        ttk.Label(input_frame, text="销售价:").grid(row=5, column=0, padx=5, pady=5)
        selling_price_var = tk.StringVar(value=item[5])
        ttk.Entry(input_frame, textvariable=selling_price_var).grid(row=5, column=1, padx=5, pady=5)
        
        # 预警值
        ttk.Label(input_frame, text="预警值:").grid(row=6, column=0, padx=5, pady=5)
        warning_level_var = tk.StringVar(value=item[7])
        ttk.Entry(input_frame, textvariable=warning_level_var).grid(row=6, column=1, padx=5, pady=5)
        
        def save_changes():
            try:
                # 获取输入值
                name = name_var.get()
                category = category_var.get().split(' - ')[0] if category_var.get() else None
                supplier = supplier_var.get().split(' - ')[0] if supplier_var.get() else None
                quantity = int(quantity_var.get())
                purchase_price = float(purchase_price_var.get())
                selling_price = float(selling_price_var.get())
                warning_level = int(warning_level_var.get())
                
                # 验证必填项
                if not name or not category:
                    messagebox.showerror('错误', '商品名称和分类为必填项')
                    return
                    
                # 验证数值
                if quantity < 0 or purchase_price < 0 or selling_price < 0 or warning_level < 0:
                    messagebox.showerror('错误', '数量、价格和预警值不能为负数')
                    return
                    
                # 更新数据
                self.cursor.execute('''
                    UPDATE inventory SET
                        name = ?, category_id = ?, supplier_id = ?,
                        quantity = ?, purchase_price = ?, selling_price = ?,
                        warning_level = ?
                    WHERE id = ?
                ''', (name, category, supplier, quantity, purchase_price,
                      selling_price, warning_level, item_id))
                
                self.conn.commit()
                self.refresh_inventory()
                self.update_product_combos()
                edit_window.destroy()
                messagebox.showinfo('成功', '商品信息更新成功')
                
            except ValueError:
                messagebox.showerror('错误', '请输入有效的数字')
            except sqlite3.Error as e:
                messagebox.showerror('错误', f'更新商品失败: {e}')
        
        # 保存按钮
        ttk.Button(input_frame, text="保存", command=save_changes).grid(row=7, column=0, columnspan=2, pady=20)

    def delete_inventory(self):
        """删除库存商品"""
        selected = self.inventory_tree.selection()
        if not selected:
            messagebox.showwarning('警告', '请选择要删除的商品')
            return
            
        item_id = self.inventory_tree.item(selected)['values'][0]
        
        # 检查是否有订单使用此商品
        self.cursor.execute('SELECT COUNT(*) FROM order_items WHERE product_id = ?', (item_id,))
        if self.cursor.fetchone()[0] > 0:
            messagebox.showerror('错误', '该商品已被订单使用，无法删除')
            return
            
        if messagebox.askyesno('确认', '确定要删除该商品吗？'):
            try:
                self.cursor.execute('DELETE FROM inventory WHERE id = ?', (item_id,))
                self.conn.commit()
                self.refresh_inventory()
                self.update_product_combos()
                messagebox.showinfo('成功', '商品删除成功')
            except sqlite3.Error as e:
                messagebox.showerror('错误', f'删除商品失败: {e}')

    def add_transaction(self):
        """添加交易记录"""
        try:
            # 获取输入值
            trans_type = self.trans_type_var.get()
            business_type = self.business_type_var.get()
            amount = float(self.amount_var.get())
            description = self.description_var.get()
            customer = self.trans_customer_var.get().split(' - ')[0] if self.trans_customer_var.get() else None
            supplier = self.trans_supplier_var.get().split(' - ')[0] if self.trans_supplier_var.get() else None
            order = self.trans_order_var.get().split(' - ')[0] if self.trans_order_var.get() else None
            date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # 验证必填项
            if not trans_type or not business_type or amount <= 0:
                messagebox.showerror('错误', '交易类型、业务类型和金额为必填项，且金额必须大于0')
                return
                
            # 插入数据
            self.cursor.execute('''
                INSERT INTO transactions (
                    date, type, business_type, amount, description,
                    customer_id, supplier_id, order_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (date, trans_type, business_type, amount, description,
                  customer, supplier, order))
            
            self.conn.commit()
            self.refresh_transactions()
            self.clear_transaction_inputs()
            messagebox.showinfo('成功', '交易记录添加成功')
            
        except ValueError:
            messagebox.showerror('错误', '请输入有效的金额')
        except sqlite3.Error as e:
            messagebox.showerror('错误', f'添加交易记录失败: {e}')

    def edit_transaction(self):
    #"""编辑交易记录"""
        try:
            # 获取输入值
            trans_type = type_var.get()
            business_type = business_type_var.get()
            amount = float(amount_var.get())
            description = description_var.get()
            customer = customer_var.get().split(' - ')[0] if customer_var.get() else None
            supplier = supplier_var.get().split(' - ')[0] if supplier_var.get() else None
            order = order_var.get().split(' - ')[0] if order_var.get() else None
            
            # 验证必填项
            if not trans_type or not business_type or amount <= 0:
                messagebox.showerror('错误', '交易类型、业务类型和金额为必填项，且金额必须大于0')
                return
                
            # 更新数据
            self.cursor.execute('''
                UPDATE transactions SET
                    type = ?, business_type = ?, amount = ?,
                    description = ?, customer_id = ?, supplier_id = ?,
                    order_id = ?
                WHERE id = ?
            ''', (trans_type, business_type, amount, description,
                customer, supplier, order, trans_id))
            
            self.conn.commit()
            self.refresh_transactions()
            edit_window.destroy()
            messagebox.showinfo('成功', '交易记录更新成功')
            
        except ValueError:
            messagebox.showerror('错误', '请输入有效的金额')
        except sqlite3.Error as e:
            messagebox.showerror('错误', f'更新交易记录失败: {e}')

    def delete_transaction(self):
        """删除交易记录"""
        selected = self.transactions_tree.selection()
        if not selected:
            messagebox.showwarning('警告', '请选择要删除的交易记录')
            return
            
        trans_id = self.transactions_tree.item(selected)['values'][0]
        
        if messagebox.askyesno('确认', '确定要删除该交易记录吗？'):
            try:
                self.cursor.execute('DELETE FROM transactions WHERE id = ?', (trans_id,))
                self.conn.commit()
                self.refresh_transactions()
                messagebox.showinfo('成功', '交易记录删除成功')
            except sqlite3.Error as e:
                messagebox.showerror('错误', f'删除交易记录失败: {e}')

    def refresh_transactions(self):
        """刷新交易记录列表"""
        for item in self.transactions_tree.get_children():
            self.transactions_tree.delete(item)
            
        self.cursor.execute('''
            SELECT t.*, c.name as customer_name, s.name as supplier_name
            FROM transactions t
            LEFT JOIN customers c ON t.customer_id = c.id
            LEFT JOIN suppliers s ON t.supplier_id = s.id
            ORDER BY t.date DESC
        ''')
        
        for row in self.cursor.fetchall():
            self.transactions_tree.insert('', 'end', values=row)

    def clear_transaction_inputs(self):
        """清空交易记录输入框"""
        self.trans_type_var.set('')
        self.business_type_var.set('')
        self.amount_var.set('')
        self.description_var.set('')
        self.trans_customer_var.set('')
        self.trans_supplier_var.set('')
        self.trans_order_var.set('')

    def add_customer(self):
        """添加客户"""
        try:
            # 获取输入值
            name = self.customer_name_var.get()
            contact = self.contact_var.get()
            customer_type = self.customer_type_var.get()
            address = self.address_var.get()
            notes = self.notes_var.get()
            
            # 验证必填项
            if not name or not customer_type:
                messagebox.showerror('错误', '客户名称和类型为必填项')
                return
                
            # 插入数据
            self.cursor.execute('''
                INSERT INTO customers (name, contact, type, address, notes)
                VALUES (?, ?, ?, ?, ?)
            ''', (name, contact, customer_type, address, notes))
            
            self.conn.commit()
            self.refresh_customers()
            self.update_customer_combos()
            self.clear_customer_inputs()
            messagebox.showinfo('成功', '客户添加成功')
            
        except sqlite3.Error as e:
            messagebox.showerror('错误', f'添加客户失败: {e}')

    def edit_customer(self):
        """编辑客户信息"""
        selected = self.customers_tree.selection()
        if not selected:
            messagebox.showwarning('警告', '请选择要编辑的客户')
            return
            
        customer_id = self.customers_tree.item(selected)['values'][0]
        
        # 获取客户信息
        self.cursor.execute('SELECT * FROM customers WHERE id = ?', (customer_id,))
        customer = self.cursor.fetchone()
        if not customer:
            messagebox.showerror('错误', '客户不存在')
            return
            
        # 创建编辑窗口
        edit_window = tk.Toplevel(self.root)
        edit_window.title("编辑客户信息")
        edit_window.geometry("500x400")
        
        # 创建输入框架
        input_frame = ttk.LabelFrame(edit_window, text="客户信息")
        input_frame.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
        
        # 客户名称
        ttk.Label(input_frame, text="客户名称:").grid(row=0, column=0, padx=5, pady=5)
        name_var = tk.StringVar(value=customer[1])
        ttk.Entry(input_frame, textvariable=name_var).grid(row=0, column=1, padx=5, pady=5)
        
        # 联系方式
        ttk.Label(input_frame, text="联系方式:").grid(row=1, column=0, padx=5, pady=5)
        contact_var = tk.StringVar(value=customer[2])
        ttk.Entry(input_frame, textvariable=contact_var).grid(row=1, column=1, padx=5, pady=5)
        
        # 客户类型
        ttk.Label(input_frame, text="客户类型:").grid(row=2, column=0, padx=5, pady=5)
        type_var = tk.StringVar(value=customer[5])
        ttk.Combobox(
            input_frame,
            textvariable=type_var,
            values=['意向客户', '已合作客户', '已联系客户'],
            state='readonly'
        ).grid(row=2, column=1, padx=5, pady=5)
        
        # 地址
        ttk.Label(input_frame, text="地址:").grid(row=3, column=0, padx=5, pady=5)
        address_var = tk.StringVar(value=customer[3])
        ttk.Entry(input_frame, textvariable=address_var).grid(row=3, column=1, padx=5, pady=5)
        
        # 备注
        ttk.Label(input_frame, text="备注:").grid(row=4, column=0, padx=5, pady=5)
        notes_var = tk.StringVar(value=customer[4])
        ttk.Entry(input_frame, textvariable=notes_var).grid(row=4, column=1, padx=5, pady=5)
        
        def save_changes():
            try:
                # 获取输入值
                name = name_var.get()
                contact = contact_var.get()
                customer_type = type_var.get()
                address = address_var.get()
                notes = notes_var.get()
                
                # 验证必填项
                if not name or not customer_type:
                    messagebox.showerror('错误', '客户名称和类型为必填项')
                    return
                    
                # 更新数据
                self.cursor.execute('''
                    UPDATE customers SET
                        name = ?, contact = ?, type = ?,
                        address = ?, notes = ?
                    WHERE id = ?
                ''', (name, contact, customer_type, address, notes, customer_id))
                
                self.conn.commit()
                self.refresh_customers()
                self.update_customer_combos()
                edit_window.destroy()
                messagebox.showinfo('成功', '客户信息更新成功')
                
            except sqlite3.Error as e:
                messagebox.showerror('错误', f'更新客户信息失败: {e}')
        
        # 保存按钮
        ttk.Button(input_frame, text="保存", command=save_changes).grid(row=5, column=0, columnspan=2, pady=20)

    def delete_customer(self):
        """删除客户"""
        selected = self.customers_tree.selection()
        if not selected:
            messagebox.showwarning('警告', '请选择要删除的客户')
            return
            
        customer_id = self.customers_tree.item(selected)['values'][0]
        
        # 检查是否有订单使用此客户
        self.cursor.execute('SELECT COUNT(*) FROM orders WHERE customer_id = ?', (customer_id,))
        if self.cursor.fetchone()[0] > 0:
            messagebox.showerror('错误', '该客户有关联订单，无法删除')
            return
            
        # 检查是否有交易记录使用此客户
        self.cursor.execute('SELECT COUNT(*) FROM transactions WHERE customer_id = ?', (customer_id,))
        if self.cursor.fetchone()[0] > 0:
            messagebox.showerror('错误', '该客户有关联交易记录，无法删除')
            return
            
        if messagebox.askyesno('确认', '确定要删除该客户吗？'):
            try:
                self.cursor.execute('DELETE FROM customers WHERE id = ?', (customer_id,))
                self.conn.commit()
                self.refresh_customers()
                self.update_customer_combos()
                messagebox.showinfo('成功', '客户删除成功')
            except sqlite3.Error as e:
                messagebox.showerror('错误', f'删除客户失败: {e}')

    def refresh_customers(self):
        """刷新客户列表"""
        for item in self.customers_tree.get_children():
            self.customers_tree.delete(item)
            
        self.cursor.execute('SELECT * FROM customers')
        for row in self.cursor.fetchall():
            self.customers_tree.insert('', 'end', values=row)

    def clear_customer_inputs(self):
        """清空客户输入框"""
        self.customer_name_var.set('')
        self.contact_var.set('')
        self.customer_type_var.set('')
        self.address_var.set('')
        self.notes_var.set('')

    def add_supplier(self):
        """添加供应商"""
        try:
            # 获取输入值
            name = self.supplier_name_var.get()
            contact = self.supplier_contact_var.get()
            supplier_type = self.supplier_type_var.get()
            address = self.supplier_address_var.get()
            notes = self.supplier_notes_var.get()
            
            # 验证必填项
            if not name or not supplier_type:
                messagebox.showerror('错误', '供应商名称和类型为必填项')
                return
                
            # 插入数据
            self.cursor.execute('''
                INSERT INTO suppliers (name, contact, type, address, notes)
                VALUES (?, ?, ?, ?, ?)
            ''', (name, contact, supplier_type, address, notes))
            
            self.conn.commit()
            self.refresh_suppliers()
            self.update_supplier_combos()
            self.clear_supplier_inputs()
            messagebox.showinfo('成功', '供应商添加成功')
            
        except sqlite3.Error as e:
            messagebox.showerror('错误', f'添加供应商失败: {e}')

    def edit_supplier(self):
        """编辑供应商信息"""
        selected = self.suppliers_tree.selection()
        if not selected:
            messagebox.showwarning('警告', '请选择要编辑的供应商')
            return
            
        supplier_id = self.suppliers_tree.item(selected)['values'][0]
        
        # 获取供应商信息
        self.cursor.execute('SELECT * FROM suppliers WHERE id = ?', (supplier_id,))
        supplier = self.cursor.fetchone()
        if not supplier:
            messagebox.showerror('错误', '供应商不存在')
            return
            
        # 创建编辑窗口
        edit_window = tk.Toplevel(self.root)
        edit_window.title("编辑供应商信息")
        edit_window.geometry("500x400")
        
        # 创建输入框架
        input_frame = ttk.LabelFrame(edit_window, text="供应商信息")
        input_frame.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
        
        # 供应商名称
        ttk.Label(input_frame, text="供应商名称:").grid(row=0, column=0, padx=5, pady=5)
        name_var = tk.StringVar(value=supplier[1])
        ttk.Entry(input_frame, textvariable=name_var).grid(row=0, column=1, padx=5, pady=5)
        
        # 联系方式
        ttk.Label(input_frame, text="联系方式:").grid(row=1, column=0, padx=5, pady=5)
        contact_var = tk.StringVar(value=supplier[2])
        ttk.Entry(input_frame, textvariable=contact_var).grid(row=1, column=1, padx=5, pady=5)
        
        # 供应商类型
        ttk.Label(input_frame, text="供应商类型:").grid(row=2, column=0, padx=5, pady=5)
        type_var = tk.StringVar(value=supplier[5])
        ttk.Combobox(
            input_frame,
            textvariable=type_var,
            values=['生产商', '代理商', '批发商'],
            state='readonly'
        ).grid(row=2, column=1, padx=5, pady=5)
        
        # 地址
        ttk.Label(input_frame, text="地址:").grid(row=3, column=0, padx=5, pady=5)
        address_var = tk.StringVar(value=supplier[3])
        ttk.Entry(input_frame, textvariable=address_var).grid(row=3, column=1, padx=5, pady=5)
        
        # 备注
        ttk.Label(input_frame, text="备注:").grid(row=4, column=0, padx=5, pady=5)
        notes_var = tk.StringVar(value=supplier[4])
        ttk.Entry(input_frame, textvariable=notes_var).grid(row=4, column=1, padx=5, pady=5)
        
        def save_changes():
            try:
                # 获取输入值
                name = name_var.get()
                contact = contact_var.get()
                supplier_type = type_var.get()
                address = address_var.get()
                notes = notes_var.get()
                
                # 验证必填项
                if not name or not supplier_type:
                    messagebox.showerror('错误', '供应商名称和类型为必填项')
                    return
                    
                # 更新数据
                self.cursor.execute('''
                    UPDATE suppliers SET
                        name = ?, contact = ?, type = ?,
                        address = ?, notes = ?
                    WHERE id = ?
                ''', (name, contact, supplier_type, address, notes, supplier_id))
                
                self.conn.commit()
                self.refresh_suppliers()
                self.update_supplier_combos()
                edit_window.destroy()
                messagebox.showinfo('成功', '供应商信息更新成功')
                
            except sqlite3.Error as e:
                messagebox.showerror('错误', f'更新供应商信息失败: {e}')
        
        # 保存按钮
        ttk.Button(input_frame, text="保存", command=save_changes).grid(row=5, column=0, columnspan=2, pady=20)

    def delete_supplier(self):
        """删除供应商"""
        selected = self.suppliers_tree.selection()
        if not selected:
            messagebox.showwarning('警告', '请选择要删除的供应商')
            return
            
        supplier_id = self.suppliers_tree.item(selected)['values'][0]
        
        # 检查是否有商品使用此供应商
        self.cursor.execute('SELECT COUNT(*) FROM inventory WHERE supplier_id = ?', (supplier_id,))
        if self.cursor.fetchone()[0] > 0:
            messagebox.showerror('错误', '该供应商有关联商品，无法删除')
            return
            
        # 检查是否有交易记录使用此供应商
        self.cursor.execute('SELECT COUNT(*) FROM transactions WHERE supplier_id = ?', (supplier_id,))
        if self.cursor.fetchone()[0] > 0:
            messagebox.showerror('错误', '该供应商有关联交易记录，无法删除')
            return
            
        if messagebox.askyesno('确认', '确定要删除该供应商吗？'):
            try:
                self.cursor.execute('DELETE FROM suppliers WHERE id = ?', (supplier_id,))
                self.conn.commit()
                self.refresh_suppliers()
                self.update_supplier_combos()
                messagebox.showinfo('成功', '供应商删除成功')
            except sqlite3.Error as e:
                messagebox.showerror('错误', f'删除供应商失败: {e}')

    def refresh_suppliers(self):
        """刷新供应商列表"""
        for item in self.suppliers_tree.get_children():
            self.suppliers_tree.delete(item)
            
        self.cursor.execute('SELECT * FROM suppliers')
        for row in self.cursor.fetchall():
            self.suppliers_tree.insert('', 'end', values=row)

    def clear_supplier_inputs(self):
        """清空供应商输入框"""
        self.supplier_name_var.set('')
        self.supplier_contact_var.set('')
        self.supplier_type_var.set('')
        self.supplier_address_var.set('')
        self.supplier_notes_var.set('')

    def add_order_item(self):
        """添加订单商品"""
        if not self.order_product_var.get():
            messagebox.showwarning('警告', '请选择商品')
            return
            
        try:
            product_id = self.order_product_var.get().split(' - ')[0]
            quantity = int(self.order_quantity_var.get())
            
            # 获取商品信息
            self.cursor.execute('SELECT name, selling_price FROM inventory WHERE id = ?', (product_id,))
            product = self.cursor.fetchone()
            if not product:
                messagebox.showerror('错误', '商品不存在')
                return
                
            # 计算小计
            subtotal = quantity * product[1]
            
            # 添加到订单明细列表
            self.order_items_tree.insert('', 'end', values=(
                product_id,
                product[0],
                quantity,
                product[1],
                subtotal
            ))
            
            # 更新总金额
            self.update_order_total()
            
        except ValueError:
            messagebox.showerror('错误', '请输入有效的数量')

    def delete_order_item(self):
        """删除订单商品"""
        selected = self.order_items_tree.selection()
        if not selected:
            messagebox.showwarning('警告', '请选择要删除的商品')
            return
            
        self.order_items_tree.delete(selected)
        self.update_order_total()

    def update_order_total(self):
        """更新订单总金额"""
        total = 0
        for item in self.order_items_tree.get_children():
            total += float(self.order_items_tree.item(item)['values'][4])
        
        # 添加运费和回扣
        try:
            freight = float(self.freight_cost_var.get())
            commission = float(self.commission_var.get())
            total = total + freight - commission
        except ValueError:
            pass
        
        self.order_total_var.set(f'{total:.2f}')

    def save_order(self):
        """保存订单"""
        try:
            # 获取输入值
            customer = self.order_customer_var.get().split(' - ')[0] if self.order_customer_var.get() else None
            business_type = self.order_business_type_var.get()
            freight_cost = float(self.freight_cost_var.get())
            commission = float(self.commission_var.get())
            notes = self.order_notes_var.get()
            date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # 验证必填项
            if not customer or not business_type:
                messagebox.showerror('错误', '客户和业务类型为必填项')
                return
                
            # 验证是否有商品
            if not self.order_items_tree.get_children():
                messagebox.showerror('错误', '请至少添加一个商品')
                return
                
            # 开始事务
            self.conn.execute('BEGIN')
            
            try:
                # 插入订单
                self.cursor.execute('''
                    INSERT INTO orders (
                        customer_id, date, business_type,
                        total_amount, freight_cost, commission, notes
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (customer, date, business_type,
                    float(self.order_total_var.get()), freight_cost,
                    commission, notes))
                
                order_id = self.cursor.lastrowid
                
                # 插入订单明细
                for item in self.order_items_tree.get_children():
                    values = self.order_items_tree.item(item)['values']
                    product_id = values[0]
                    quantity = values[2]
                    price = values[3]
                    
                    self.cursor.execute('''
                        INSERT INTO order_items (
                            order_id, product_id, quantity, price
                        ) VALUES (?, ?, ?, ?)
                    ''', (order_id, product_id, quantity, price))
                    
                    # 更新库存
                    self.cursor.execute('''
                        UPDATE inventory
                        SET quantity = quantity - ?
                        WHERE id = ?
                    ''', (quantity, product_id))
                
                # 提交事务
                self.conn.commit()
                
                # 刷新界面
                self.refresh_orders()
                self.clear_order_inputs()
                self.update_order_combo()
                messagebox.showinfo('成功', '订单保存成功')
                
            except sqlite3.Error as e:
                # 回滚事务
                self.conn.rollback()
                raise e
                
        except ValueError:
            messagebox.showerror('错误', '请输入有效的数字')
        except sqlite3.Error as e:
            messagebox.showerror('错误', f'保存订单失败: {e}')

    def edit_order(self):
        """编辑订单"""
        selected = self.orders_tree.selection()
        if not selected:
            messagebox.showwarning('警告', '请选择要编辑的订单')
            return
            
        order_id = self.orders_tree.item(selected)['values'][0]
        
        # 获取订单信息
        self.cursor.execute('''
            SELECT o.*, c.name as customer_name
            FROM orders o
            JOIN customers c ON o.customer_id = c.id
            WHERE o.id = ?
        ''', (order_id,))
        
        order = self.cursor.fetchone()
        if not order:
            messagebox.showerror('错误', '订单不存在')
            return
            
        # 创建编辑窗口
        edit_window = tk.Toplevel(self.root)
        edit_window.title("编辑订单")
        edit_window.geometry("800x600")
        
        # 创建输入框架
        input_frame = ttk.LabelFrame(edit_window, text="订单信息")
        input_frame.pack(padx=10, pady=10, fill=tk.X)
        
        # 第一行
        row1 = ttk.Frame(input_frame)
        row1.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(row1, text="客户:").pack(side=tk.LEFT, padx=5)
        customer_var = tk.StringVar(value=f"{order[1]} - {order[-1]}")
        customer_combo = ttk.Combobox(
            row1,
            textvariable=customer_var,
            values=self.order_customer_combo['values'],
            state='readonly'
        )
        customer_combo.pack(side=tk.LEFT, padx=5)
        
        ttk.Label(row1, text="业务类型:").pack(side=tk.LEFT, padx=5)
        business_type_var = tk.StringVar(value=order[3])
        ttk.Combobox(
            row1,
            textvariable=business_type_var,
            values=['对公', '对私'],
            state='readonly'
        ).pack(side=tk.LEFT, padx=5)
        
        # 第二行
        row2 = ttk.Frame(input_frame)
        row2.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(row2, text="运费:").pack(side=tk.LEFT, padx=5)
        freight_cost_var = tk.StringVar(value=order[5])
        ttk.Entry(row2, textvariable=freight_cost_var).pack(side=tk.LEFT, padx=5)
        
        ttk.Label(row2, text="回扣:").pack(side=tk.LEFT, padx=5)
        commission_var = tk.StringVar(value=order[6])
        ttk.Entry(row2, textvariable=commission_var).pack(side=tk.LEFT, padx=5)
        
        # 第三行
        row3 = ttk.Frame(input_frame)
        row3.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(row3, text="备注:").pack(side=tk.LEFT, padx=5)
        notes_var = tk.StringVar(value=order[7])
        ttk.Entry(row3, textvariable=notes_var, width=50).pack(side=tk.LEFT, padx=5)
        
        # 创建订单明细框架
        detail_frame = ttk.LabelFrame(edit_window, text="订单明细")
        detail_frame.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
        
        # 创建订单明细列表
        items_tree = ttk.Treeview(
            detail_frame,
            columns=('ID', '商品名称', '数量', '单价', '小计'),
            show='headings',
            height=10
        )
        
        # 设置列标题
        items_tree.heading('ID', text='ID')
        items_tree.heading('商品名称', text='商品名称')
        items_tree.heading('数量', text='数量')
        items_tree.heading('单价', text='单价')
        items_tree.heading('小计', text='小计')
        
        # 设置列宽
        for col in items_tree['columns']:
            items_tree.column(col, width=100)
        
        items_tree.pack(fill=tk.BOTH, expand=True)
        
        # 获取订单明细
        self.cursor.execute('''
            SELECT oi.*, i.name
            FROM order_items oi
            JOIN inventory i ON oi.product_id = i.id
            WHERE oi.order_id = ?
        ''', (order_id,))
        
        for item in self.cursor.fetchall():
            items_tree.insert('', 'end', values=(
                item[2],  # product_id
                item[-1],  # product_name
                item[3],  # quantity
                item[4],  # price
                item[3] * item[4]  # subtotal
            ))
        
        # 商品选择框架
        product_frame = ttk.Frame(detail_frame)
        product_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(product_frame, text="商品:").pack(side=tk.LEFT, padx=5)
        product_var = tk.StringVar()
        product_combo = ttk.Combobox(
            product_frame,
            textvariable=product_var,
            values=self.order_product_combo['values'],
            state='readonly'
        )
        product_combo.pack(side=tk.LEFT, padx=5)
        
        ttk.Label(product_frame, text="数量:").pack(side=tk.LEFT, padx=5)
        quantity_var = tk.StringVar(value='1')
        ttk.Entry(product_frame, textvariable=quantity_var).pack(side=tk.LEFT, padx=5)
        
        def add_item():
            if not product_var.get():
                messagebox.showwarning('警告', '请选择商品')
                return
                
            #try```python
            try:
                product_id = product_var.get().split(' - ')[0]
                quantity = int(quantity_var.get())
                
                # 获取商品信息
                self.cursor.execute('SELECT name, selling_price FROM inventory WHERE id = ?', (product_id,))
                product = self.cursor.fetchone()
                if not product:
                    messagebox.showerror('错误', '商品不存在')
                    return
                    
                # 计算小计
                subtotal = quantity * product[1]
                
                # 添加到订单明细列表
                items_tree.insert('', 'end', values=(
                    product_id,
                    product[0],
                    quantity,
                    product[1],
                    subtotal
                ))
                
                # 更新总金额
                update_total()
                
            except ValueError:
                messagebox.showerror('错误', '请输入有效的数量')
        
        def delete_item():
            selected = items_tree.selection()
            if not selected:
                messagebox.showwarning('警告', '请选择要删除的商品')
                return
                
            items_tree.delete(selected)
            update_total()
        
        def update_total():
            total = 0
            for item in items_tree.get_children():
                total += float(items_tree.item(item)['values'][4])
            
            try:
                freight = float(freight_cost_var.get())
                commission = float(commission_var.get())
                total = total + freight - commission
            except ValueError:
                pass
            
            total_var.set(f'{total:.2f}')
        
        ttk.Button(product_frame, text='添加商品', command=add_item).pack(side=tk.LEFT, padx=5)
        ttk.Button(product_frame, text='删除商品', command=delete_item).pack(side=tk.LEFT, padx=5)
        
        # 总金额显示
        total_frame = ttk.Frame(detail_frame)
        total_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(total_frame, text="总金额:").pack(side=tk.LEFT, padx=5)
        total_var = tk.StringVar(value=order[4])
        ttk.Label(total_frame, textvariable=total_var).pack(side=tk.LEFT, padx=5)
        
        def save_changes():
            try:
                # 获取输入值
                customer = customer_var.get().split(' - ')[0]
                business_type = business_type_var.get()
                freight_cost = float(freight_cost_var.get())
                commission = float(commission_var.get())
                notes = notes_var.get()
                
                # 验证必填项
                if not customer or not business_type:
                    messagebox.showerror('错误', '客户和业务类型为必填项')
                    return
                    
                # 验证是否有商品
                if not items_tree.get_children():
                    messagebox.showerror('错误', '请至少添加一个商品')
                    return
                    
                # 开始事务
                self.conn.execute('BEGIN')
                
                try:
                    # 更新订单
                    self.cursor.execute('''
                        UPDATE orders SET
                            customer_id = ?, business_type = ?,
                            total_amount = ?, freight_cost = ?,
                            commission = ?, notes = ?
                        WHERE id = ?
                    ''', (customer, business_type,
                        float(total_var.get()), freight_cost,
                        commission, notes, order_id))
                    
                    # 删除原有订单明细
                    self.cursor.execute('DELETE FROM order_items WHERE order_id = ?', (order_id,))
                    
                    # 插入新的订单明细
                    for item in items_tree.get_children():
                        values = items_tree.item(item)['values']
                        product_id = values[0]
                        quantity = values[2]
                        price = values[3]
                        
                        self.cursor.execute('''
                            INSERT INTO order_items (
                                order_id, product_id, quantity, price
                            ) VALUES (?, ?, ?, ?)
                        ''', (order_id, product_id, quantity, price))
                        
                        # 更新库存
                        self.cursor.execute('''
                            UPDATE inventory
                            SET quantity = quantity - ?
                            WHERE id = ?
                        ''', (quantity, product_id))
                    
                    # 提交事务
                    self.conn.commit()
                    
                    # 刷新界面
                    self.refresh_orders()
                    edit_window.destroy()
                    messagebox.showinfo('成功', '订单更新成功')
                    
                except sqlite3.Error as e:
                    # 回滚事务
                    self.conn.rollback()
                    raise e
                    
            except ValueError:
                messagebox.showerror('错误', '请输入有效的数字')
            except sqlite3.Error as e:
                messagebox.showerror('错误', f'更新订单失败: {e}')
        
        # 保存按钮
        ttk.Button(edit_window, text="保存", command=save_changes).pack(pady=10)

    def delete_order(self):
        """删除订单"""
        selected = self.orders_tree.selection()
        if not selected:
            messagebox.showwarning('警告', '请选择要删除的订单')
            return
            
        order_id = self.orders_tree.item(selected)['values'][0]
        
        # 检查是否有交易记录使用此订单
        self.cursor.execute('SELECT COUNT(*) FROM transactions WHERE order_id = ?', (order_id,))
        if self.cursor.fetchone()[0] > 0:
            messagebox.showerror('错误', '该订单有关联交易记录，无法删除')
            return
            
        if messagebox.askyesno('确认', '确定要删除该订单吗？'):
            try:
                # 开始事务
                self.conn.execute('BEGIN')
                
                try:
                    # 删除订单明细
                    self.cursor.execute('DELETE FROM order_items WHERE order_id = ?', (order_id,))
                    
                    # 删除订单
                    self.cursor.execute('DELETE FROM orders WHERE id = ?', (order_id,))
                    
                    # 提交事务
                    self.conn.commit()
                    
                    # 刷新界面
                    self.refresh_orders()
                    self.update_order_combo()
                    messagebox.showinfo('成功', '订单删除成功')
                    
                except sqlite3.Error as e:
                    # 回滚事务
                    self.conn.rollback()
                    raise e
                    
            except sqlite3.Error as e:
                messagebox.showerror('错误', f'删除订单失败: {e}')

    def refresh_orders(self):
        """刷新订单列表"""
        for item in self.orders_tree.get_children():
            self.orders_tree.delete(item)
            
        self.cursor.execute('''
            SELECT o.*, c.name as customer_name
            FROM orders o
            JOIN customers c ON o.customer_id = c.id
            ORDER BY o.date DESC
        ''')
        
        for row in self.cursor.fetchall():
            self.orders_tree.insert('', 'end', values=row)

    def clear_order_inputs(self):
        """清空订单输入框"""
        self.order_customer_var.set('')
        self.order_business_type_var.set('')
        self.freight_cost_var.set('0.0')
        self.commission_var.set('0.0')
        self.order_notes_var.set('')
        self.order_product_var.set('')
        self.order_quantity_var.set('1')
        
        for item in self.order_items_tree.get_children():
            self.order_items_tree.delete(item)
        
        self.order_total_var.set('0.00')

    def init_account_set_selector(self):
        """初始化账套选择器"""
        selector_frame = ttk.Frame(self.root)
        selector_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(selector_frame, text="当前账套:").pack(side=tk.LEFT, padx=5)
        
        self.account_set_var = tk.StringVar(value=self.account_sets[0])
        account_set_combo = ttk.Combobox(
            selector_frame,
            textvariable=self.account_set_var,
            values=self.account_sets,
            state='readonly'
        )
        account_set_combo.pack(side=tk.LEFT, padx=5)
        
        def on_account_set_change(event):
            self.current_db_file = f"{self.account_set_var.get()}.db"
            self.init_database()
            self.refresh_all()
        
        account_set_combo.bind('<<ComboboxSelected>>', on_account_set_change)

    def refresh_all(self):
        """刷新所有数据"""
        self.refresh_categories()
        self.refresh_inventory()
        self.refresh_transactions()
        self.refresh_customers()
        self.refresh_suppliers()
        self.refresh_orders()
        self.refresh_all_combos()


if __name__ == '__main__':
    root = tk.Tk()
    app = InventorySystem(root)
    root.mainloop()