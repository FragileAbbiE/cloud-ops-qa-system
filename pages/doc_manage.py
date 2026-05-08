import os
import streamlit as st
from utils.auth import get_current_user, require_admin
from utils.db import (
    add_document_record, list_documents, delete_document,
    list_product_lines, list_components, list_doc_types,
    add_product_line, delete_product_line,
    add_component, delete_component,
    add_doc_type, delete_doc_type
)

try:
    from src.data_processor import DataProcessor
except Exception:
    DataProcessor = None

user = get_current_user()
if not user:
    st.error("请先登录")
    st.stop()

if not require_admin(user):
    st.error("无权访问")
    st.stop()

st.subheader("文档管理")

UPLOAD_DIR = os.path.join("data", "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

with st.expander("上传文档", expanded=True):
    files = st.file_uploader(
        "支持 PDF / Word / Markdown",
        type=["pdf", "doc", "docx", "md", "markdown"],
        accept_multiple_files=True
    )

    product_lines = list_product_lines()
    doc_types = list_doc_types()

    if not product_lines:
        st.warning("请先在下方「维护标签」中添加产品线")
        st.stop()

    pl_names = [pl["name"] for pl in product_lines]
    selected_pl_name = st.selectbox("产品线", pl_names)
    selected_pl_id = next(pl["id"] for pl in product_lines if pl["name"] == selected_pl_name)

    components = list_components(product_line_id=selected_pl_id)
    if components:
        component_names = [c["name"] for c in components]
        component_name = st.selectbox("组件", component_names)
    else:
        st.warning(f"产品线「{selected_pl_name}」下暂无组件，请先在「维护标签」中添加")
        component_name = st.text_input("或临时输入组件名")

    dt_names = [dt["name"] for dt in doc_types] if doc_types else ["故障排障"]
    doc_type = st.selectbox("文档类型", dt_names)

    if st.button("开始处理", type="primary"):
        if not files:
            st.warning("请先选择文件")
        else:
            progress = st.progress(0, text="开始处理...")
            total = len(files)
            ok_count = 0

            processor = DataProcessor() if DataProcessor is not None else None
            if processor is None:
                st.warning("未检测到 src.data_processor，当前仅执行文件上传与登记，不做向量化入库。")

            for i, f in enumerate(files, 1):
                save_path = os.path.join(UPLOAD_DIR, f.name)
                with open(save_path, "wb") as wf:
                    wf.write(f.getbuffer())

                progress.progress((i - 1) / total + 0.2 / total, text=f"上传中：{f.name}")

                if processor is not None and hasattr(processor, "process_single_file"):
                    try:
                        processor.process_single_file(
                            file_path=save_path,
                            product_line=selected_pl_name,
                            component=component_name,
                            doc_type=doc_type
                        )
                        progress.progress((i - 1) / total + 0.8 / total, text=f"向量化中：{f.name}")
                    except Exception as e:
                        st.error(f"处理 {f.name} 失败：{e}")
                        continue
                elif processor is not None:
                    st.warning("DataProcessor 未实现 process_single_file()，已跳过向量化。")

                add_document_record(
                    filename=f.name,
                    file_path=save_path,
                    file_size=f.size,
                    uploaded_by=user["id"],
                    product_line=selected_pl_name,
                    component=component_name,
                    doc_type=doc_type
                )

                ok_count += 1
                progress.progress(i / total, text=f"完成：{f.name}")

            st.success(f"上传处理完成，成功 {ok_count}/{total} 个文件。")

st.caption("已入库文档")
docs = list_documents()
st.dataframe(docs, use_container_width=True)

if docs:
    id_list = [d["id"] for d in docs]
    del_id = st.selectbox("选择要删除的文档 ID", id_list)

    if st.button("删除文档"):
        delete_document(del_id)
        st.success(f"文档 {del_id} 已删除")
        st.rerun()

st.divider()
st.subheader("维护标签")
st.caption("管理产品线、组件与文档类型的元数据标签配置")

tab1, tab2, tab3 = st.tabs(["产品线", "组件", "文档类型"])

with tab1:
    st.markdown("##### 当前产品线列表")
    pls = list_product_lines()
    if pls:
        st.dataframe(pls, use_container_width=True, hide_index=True)
    else:
        st.info("暂无产品线，请添加")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("##### 添加产品线")
        with st.form("add_pl_form", clear_on_submit=True):
            new_pl_name = st.text_input("产品线名称（英文，如 Kafka_MQ）")
            new_pl_desc = st.text_input("描述（可选）")
            if st.form_submit_button("添加", type="primary"):
                if not new_pl_name.strip():
                    st.warning("名称不能为空")
                else:
                    try:
                        add_product_line(new_pl_name.strip(), new_pl_desc.strip())
                        st.success(f"已添加：{new_pl_name}")
                        st.rerun()
                    except Exception:
                        st.error("添加失败：名称可能重复")

    with col2:
        st.markdown("##### 删除产品线")
        if pls:
            del_pl_id = st.selectbox(
                "选择要删除的产品线",
                [pl["id"] for pl in pls],
                format_func=lambda x: next(pl["name"] for pl in pls if pl["id"] == x),
                key="del_pl_select"
            )
            st.caption("⚠️ 删除产品线将级联删除其下所有组件")
            if st.button("确认删除", key="del_pl_btn"):
                delete_product_line(del_pl_id)
                st.success("已删除")
                st.rerun()

with tab2:
    st.markdown("##### 当前组件列表")

    # 筛选区
    filter_col1, filter_col2 = st.columns([1, 1])

    pls_for_comp = list_product_lines()
    pl_options = ["全部产品线"] + [pl["name"] for pl in pls_for_comp]

    with filter_col1:
        selected_pl_name = st.selectbox(
            "按产品线筛选",
            pl_options,
            key="filter_pl"
        )

    with filter_col2:
        search_kw = st.text_input(
            "搜索组件名",
            key="search_comp",
            placeholder="输入关键词进行模糊匹配"
        )

    # 先按产品线过滤（数据库层）
    if selected_pl_name == "全部产品线":
        comps = list_components()
    else:
        selected_pl = next((pl for pl in pls_for_comp if pl["name"] == selected_pl_name), None)
        if selected_pl:
            comps = list_components(product_line_id=selected_pl["id"])
        else:
            comps = []

    # 再按关键词过滤（内存层，不区分大小写）
    kw = (search_kw or "").strip().lower()
    if kw:
        comps = [c for c in comps if kw in c["name"].lower()]

    st.caption(f"共 {len(comps)} 个组件")

    if comps:
        st.dataframe(
            [{"产品线": c["product_line"], "组件名": c["name"]} for c in comps],
            use_container_width=True, hide_index=True
        )
    else:
        st.info("暂无符合条件的组件")

    if not pls_for_comp:
        st.warning("请先添加产品线")
    else:
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("##### 添加组件")
            with st.form("add_comp_form", clear_on_submit=True):
                comp_pl_id = st.selectbox(
                    "所属产品线",
                    [pl["id"] for pl in pls_for_comp],
                    format_func=lambda x: next(pl["name"] for pl in pls_for_comp if pl["id"] == x)
                )
                new_comp_name = st.text_input("组件名称")
                if st.form_submit_button("添加", type="primary"):
                    if not new_comp_name.strip():
                        st.warning("名称不能为空")
                    else:
                        try:
                            add_component(comp_pl_id, new_comp_name.strip())
                            st.success(f"已添加：{new_comp_name}")
                            st.rerun()
                        except Exception:
                            st.error("添加失败：名称可能重复")

        with col2:
            st.markdown("##### 删除组件")
            if comps:
                del_comp_id = st.selectbox(
                    "选择要删除的组件",
                    [c["id"] for c in comps],
                    format_func=lambda x: next(f"{c['product_line']} / {c['name']}" for c in comps if c["id"] == x),
                    key="del_comp_select"
                )
                if st.button("确认删除", key="del_comp_btn"):
                    delete_component(del_comp_id)
                    st.success("已删除")
                    st.rerun()
            else:
                st.info("当前筛选条件下无可删除的组件")

with tab3:
    st.markdown("##### 当前文档类型列表")
    dts = list_doc_types()
    if dts:
        st.dataframe(dts, use_container_width=True, hide_index=True)
    else:
        st.info("暂无文档类型，请添加")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("##### 添加文档类型")
        with st.form("add_dt_form", clear_on_submit=True):
            new_dt_name = st.text_input("文档类型名称（如：安全加固）")
            if st.form_submit_button("添加", type="primary"):
                if not new_dt_name.strip():
                    st.warning("名称不能为空")
                else:
                    try:
                        add_doc_type(new_dt_name.strip())
                        st.success(f"已添加：{new_dt_name}")
                        st.rerun()
                    except Exception:
                        st.error("添加失败：名称可能重复")

    with col2:
        st.markdown("##### 删除文档类型")
        if dts:
            del_dt_id = st.selectbox(
                "选择要删除的文档类型",
                [dt["id"] for dt in dts],
                format_func=lambda x: next(dt["name"] for dt in dts if dt["id"] == x),
                key="del_dt_select"
            )
            if st.button("确认删除", key="del_dt_btn"):
                delete_doc_type(del_dt_id)
                st.success("已删除")
                st.rerun()
