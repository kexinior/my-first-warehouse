import streamlit as st
import pandas as pd
import os

# 设置页面配置
st.set_page_config(page_title="原神周本材料管理系统", page_icon="✨")

# 文件路径
DATA_FILE = '原神.xlsx'
META_FILE = '1.xlsx'

def load_data():
    try:
        # 读取材料名称对照表
        df_meta = pd.read_excel(META_FILE)
        
        # 读取当前数量表
        # 假设第一列是索引或标签，我们主要关注数据列
        df_counts = pd.read_excel(DATA_FILE)
        
        # 修正列名
        if '阿佩普的绿洲守望者' in df_counts.columns:
            df_counts.rename(columns={'阿佩普的绿洲守望者': '绿洲守望者'}, inplace=True)

        return df_meta, df_counts
    except Exception as e:
        st.error(f"读取文件失败: {e}")
        return None, None

def save_data(df_counts):
    try:
        df_counts.to_excel(DATA_FILE, index=False)
        st.success("数据保存成功！")
    except Exception as e:
        st.error(f"保存文件失败: {e}")

def main():
    st.title("✨ 原神周本材料管理系统")

    if not os.path.exists(DATA_FILE) or not os.path.exists(META_FILE):
        st.error(f"找不到文件，请确保 {DATA_FILE} 和 {META_FILE} 在当前目录下。")
        return

    df_meta, df_counts = load_data()
    if df_meta is None or df_counts is None:
        return

    # --- 数据预处理 ---
    # 建立周本简称(原神.xlsx列名)到全称和材料的映射
    # 原神.xlsx 的列：['怪物', '风魔龙', '北风狼', ...]
    # 1.xlsx 的列：['周本名称', '材料名称']
    
    # 获取原神.xlsx中的周本列名（排除第一列 '怪物'）
    boss_columns = [col for col in df_counts.columns if col != '怪物']
    
    # 解析 1.xlsx 获取材料名称
    # 假设 1.xlsx 的顺序和 原神.xlsx 的列顺序是一致的，或者我们需要通过名称匹配
    # 观察之前的输出，1.xlsx 每3行对应一个周本
    
    boss_materials = {}
    
    # 这里我们需要一个映射关系，因为两个表的名字可能不完全一样
    # 根据之前的 inspect 结果手动建立映射或按顺序映射
    # 既然用户说 "它的名称和原神表格的材料数量对应"，我们假设顺序是一致的
    # 原神.xlsx 的列顺序：风魔龙, 北风狼, 若陀龙王, 公子, 雷电将军, ...
    # 1.xlsx 的行顺序：风魔龙(3行), 北风狼(3行), ...
    
    # 检查长度匹配
    if len(boss_columns) * 3 > len(df_meta):
        st.warning("警告：材料名称表行数少于周本数列数，可能无法完全匹配。")
    
    for i, boss_col in enumerate(boss_columns):
        start_idx = i * 3
        if start_idx + 2 < len(df_meta):
            # 获取对应的3个材料名称
            materials = df_meta.iloc[start_idx:start_idx+3]['材料名称'].tolist()
            full_name = df_meta.iloc[start_idx]['周本名称']
            boss_materials[boss_col] = {
                'full_name': full_name,
                'materials': materials
            }
        else:
            boss_materials[boss_col] = {
                'full_name': boss_col,
                'materials': ['材料1', '材料2', '材料3']
            }

    # --- 初始化 Session State ---
    if 'completed_bosses' not in st.session_state:
        st.session_state.completed_bosses = []

    # --- 计算最少数量的周本 ---
    # 重新计算总计，防止表格里的总计行不准确
    # 取前3行数据 (索引 0, 1, 2)
    current_counts = df_counts.iloc[0:3, 1:].fillna(0) # 忽略第一列'怪物'
    
    # 计算每列的总和并排序
    sums = current_counts.sum(axis=0).sort_values()
    
    # 过滤掉本周已打的周本
    remaining_sums = sums.drop(st.session_state.completed_bosses, errors='ignore')
    
    # 取前3个（如果不足3个则取全部）
    top_n = 3
    top_bosses = remaining_sums.head(top_n)
    
    # --- 界面显示 ---
    
    # 显示本周进度
    completed_count = len(st.session_state.completed_bosses)
    st.progress(min(completed_count / 3, 1.0), text=f"本周进度: {completed_count}/3")
    
    if completed_count >= 3:
        st.success("🎉 本周三个周本任务已完成！")
        if st.button("开启新的一周 (重置进度)"):
            st.session_state.completed_bosses = []
            st.rerun()
    else:
        st.header("📊 推荐周本 (最少材料 Top 3)")
        
        if top_bosses.empty:
            st.info("所有周本都已打完？")
        else:
            cols = st.columns(len(top_bosses))
            for i, (boss_name, total_count) in enumerate(top_bosses.items()):
                with cols[i]:
                    st.metric(label=f"第 {i+1} 名: {boss_name}", value=int(total_count))
            
    st.divider()
    
    st.header("📝 录入战利品")
    
    # 选择周本
    # 默认选择最少的那个 (从 remaining_sums 里选)
    default_index = 0
    if not top_bosses.empty:
        first_boss = top_bosses.index[0]
        if first_boss in boss_columns:
            default_index = boss_columns.index(first_boss)
    
    # 如果已完成3个，虽然不推荐了，但用户可能还想补录，所以下拉框依然可用，只是默认值可能需要调整
    # 如果 top_bosses 为空（比如全打完了），默认值就随缘了
    
    selected_boss = st.selectbox("选择刚才打的周本", boss_columns, index=default_index)
    
    if selected_boss:
        if selected_boss in st.session_state.completed_bosses:
            st.warning(f"注意：'{selected_boss}' 本周已标记为完成。")

        info = boss_materials.get(selected_boss, {})
        materials = info.get('materials', [])
        full_name = info.get('full_name', '')
        
        st.caption(f"全称: {full_name}")
        
        col1, col2, col3 = st.columns(3)
        
        inputs = []
        with col1:
            v1 = st.number_input(f"{materials[0]}", min_value=0, value=0, step=1)
            inputs.append(v1)
        with col2:
            v2 = st.number_input(f"{materials[1]}", min_value=0, value=0, step=1)
            inputs.append(v2)
        with col3:
            v3 = st.number_input(f"{materials[2]}", min_value=0, value=0, step=1)
            inputs.append(v3)
            
        if st.button("提交更新", type="primary"):
            if sum(inputs) == 0:
                st.warning("请输入获得的材料数量")
            else:
                # 更新 DataFrame
                # 找到对应的列 selected_boss
                # 更新 0, 1, 2 行
                col_idx = df_counts.columns.get_loc(selected_boss)
                
                old_v1 = df_counts.iloc[0, col_idx]
                old_v2 = df_counts.iloc[1, col_idx]
                old_v3 = df_counts.iloc[2, col_idx]
                
                # 处理 NaN
                if pd.isna(old_v1): old_v1 = 0
                if pd.isna(old_v2): old_v2 = 0
                if pd.isna(old_v3): old_v3 = 0
                
                df_counts.iloc[0, col_idx] = old_v1 + inputs[0]
                df_counts.iloc[1, col_idx] = old_v2 + inputs[1]
                df_counts.iloc[2, col_idx] = old_v3 + inputs[2]
                
                # 更新总计行 (假设是第4行，索引3)
                # 也可以动态查找 '怪物' 列为 '总计' 的行
                total_row_idx = df_counts[df_counts['怪物'] == '总计'].index
                if not total_row_idx.empty:
                    idx = total_row_idx[0]
                    new_total = (old_v1 + inputs[0]) + (old_v2 + inputs[1]) + (old_v3 + inputs[2])
                    df_counts.iloc[idx, col_idx] = new_total
                
                save_data(df_counts)
                
                # 记录已完成
                if selected_boss not in st.session_state.completed_bosses:
                    st.session_state.completed_bosses.append(selected_boss)
                
                st.balloons()
                # 强制刷新页面以显示最新数据
                st.rerun()

    st.divider()
    st.header("📦 仓库管理 (直接修改)")
    
    # 模仿图片布局，使用多列展示
    # 根据屏幕宽度，这里设置为 3 列
    cols = st.columns(3)
    
    for i, boss in enumerate(boss_columns):
        with cols[i % 3]:
            with st.container(border=True):
                info = boss_materials.get(boss, {})
                full_name = info.get('full_name', boss)
                materials = info.get('materials', ['?', '?', '?'])
                
                st.subheader(boss)
                st.caption(full_name)
                
                # 获取该周本在 DataFrame 中的列索引
                col_idx = df_counts.columns.get_loc(boss)

                # 计算并显示总计
                c1 = df_counts.iloc[0, col_idx]
                c2 = df_counts.iloc[1, col_idx]
                c3 = df_counts.iloc[2, col_idx]
                total_val = (0 if pd.isna(c1) else int(c1)) + \
                            (0 if pd.isna(c2) else int(c2)) + \
                            (0 if pd.isna(c3) else int(c3))
                st.markdown(f"**总计: :blue[{total_val}]**")
                
                # 遍历3个材料
                for row_idx in range(3):
                    mat_name = materials[row_idx]
                    # 获取当前值
                    current_val = df_counts.iloc[row_idx, col_idx]
                    if pd.isna(current_val): current_val = 0
                    
                    # 创建数字输入框，允许直接修改
                    # key 必须唯一
                    new_val = st.number_input(
                        f"{mat_name}",
                        min_value=0,
                        value=int(current_val),
                        step=1,
                        key=f"edit_{boss}_{row_idx}"
                    )
                    
                    # 检测变化并保存
                    if new_val != int(current_val):
                        df_counts.iloc[row_idx, col_idx] = new_val
                        
                        # 重新计算该列的总计
                        c1 = df_counts.iloc[0, col_idx]
                        c2 = df_counts.iloc[1, col_idx]
                        c3 = df_counts.iloc[2, col_idx]
                        # 处理可能存在的 NaN (虽然刚赋了值应该不会，但为了健壮性)
                        c1 = 0 if pd.isna(c1) else c1
                        c2 = 0 if pd.isna(c2) else c2
                        c3 = 0 if pd.isna(c3) else c3
                        
                        new_total = c1 + c2 + c3
                        
                        # 更新总计行
                        total_row_idx = df_counts[df_counts['怪物'] == '总计'].index
                        if not total_row_idx.empty:
                            df_counts.iloc[total_row_idx[0], col_idx] = new_total
                            
                        save_data(df_counts)
                        st.toast(f"✅ 已更新 {boss} - {mat_name} 为 {new_val}")
                        # 这里不需要 rerun，因为输入框的值已经变了，下次加载会读到新的文件

if __name__ == "__main__":
    main()
