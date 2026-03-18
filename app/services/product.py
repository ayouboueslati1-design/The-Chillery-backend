from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status
from typing import List, Tuple, Optional
from slugify import slugify
import logging
from app.models.product import Product
from app.repositories.product import ProductRepository
from app.repositories.category import CategoryRepository
from app.repositories.review import ReviewRepository
from app.schemas.product import ProductCreate, ProductUpdate
from app.models.category import Category
from app.models.product_image import ProductImage
from app.models.review import Review

logger = logging.getLogger(__name__)


class ProductService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.product_repo = ProductRepository(Product)
        self.category_repo = CategoryRepository(Category)
        self.review_repo = ReviewRepository(Review)

    async def create_product(self, data: ProductCreate) -> Product:
        slug = slugify(data.name)
        existing = await self.product_repo.get_by_slug(self.db, slug)
        if existing:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Product name already exists.")
            
        if data.category_id:
            cat = await self.category_repo.get(self.db, str(data.category_id))
            if not cat:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found.")

        # Convert schemas to dict to manually add slug
        obj_in = data.model_dump()
        image_urls = obj_in.pop("image_urls", [])

        obj_in["slug"] = slug
        if data.category_id:
            obj_in["category_id"] = str(data.category_id)
        
        new_product = Product(**obj_in)
        self.db.add(new_product)
        await self.db.flush()
        
        for idx, url in enumerate(image_urls):
            img = ProductImage(product_id=new_product.id, url=url, sort_order=idx)
            self.db.add(img)
            
        await self.db.commit()
        # Re-fetch with eagerly loaded relationships (images, category)
        return await self.product_repo.get_by_slug(self.db, slug)

    async def get_products(
        self,
        skip: int = 0,
        limit: int = 50,
        category_slug: Optional[str] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        in_stock: Optional[bool] = None,
        search: Optional[str] = None,
        sort_by: str = "newest"
    ) -> Tuple[List[Product], int]:
        
        category_id_str = None
        if category_slug:
            cat = await self.category_repo.get_by_slug(self.db, category_slug)
            if not cat:
                return [], 0
            category_id_str = str(cat.id)

        return await self.product_repo.get_multi_with_filters(
            self.db, skip=skip, limit=limit, 
            category_id=category_id_str, min_price=min_price, max_price=max_price,
            in_stock=in_stock, search=search, sort_by=sort_by
        )

    async def get_product_by_slug(self, slug: str) -> Product:
        prod = await self.product_repo.get_by_slug(self.db, slug)
        if not prod:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found.")
        return prod

    async def get_product_by_id(self, product_id: str) -> Product:
        """Fetch a product by ID, raising 404 if not found."""
        prod = await self.product_repo.get_by_id(self.db, product_id)
        if not prod:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found.")
        return prod

    async def get_review_stats(self, product_id: str) -> Tuple[int, float]:
        """Return (count, average_rating) for a product's approved reviews."""
        return await self.review_repo.get_product_review_stats(self.db, product_id)
        return prod

    async def update_product(self, product_id: str, data: ProductUpdate) -> Product:
        prod = await self.product_repo.get(self.db, product_id)
        if not prod:
             raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found.")

        logger.debug("Updating product %s", product_id)
        update_data = data.model_dump(exclude_unset=True)
        image_urls = update_data.pop("image_urls", None)
        
        if image_urls is not None:
            logger.debug("Updating image list for product %s", product_id)
        
        if "name" in update_data and update_data["name"]:
            new_slug = slugify(update_data["name"])
            if new_slug != prod.slug:
                existing = await self.product_repo.get_by_slug(self.db, new_slug)
                if existing:
                    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="New product name already exists.")
                update_data["slug"] = new_slug

        if "category_id" in update_data and update_data["category_id"]:
            cat = await self.category_repo.get(self.db, str(update_data["category_id"]))
            if not cat:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found.")
            update_data["category_id"] = str(update_data["category_id"])

        updated = await self.product_repo.update(self.db, db_obj=prod, obj_in=update_data)
        
        if image_urls is not None:
            from sqlalchemy import delete
            await self.db.execute(
                delete(ProductImage).where(ProductImage.product_id == prod.id)
            )
            
            for idx, url in enumerate(image_urls):
                img = ProductImage(product_id=prod.id, url=url, sort_order=idx)
                self.db.add(img)
                
            await self.db.commit()
        else:
            await self.db.commit()

        # Re-fetch with eagerly loaded relationships
        return await self.product_repo.get_by_slug(self.db, updated.slug)

    async def delete_product(self, product_id: str):
         prod = await self.product_repo.get(self.db, product_id)
         if not prod:
             raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found.")
         
         # Soft delete
         prod.is_active = False
         self.db.add(prod)
         await self.db.commit()

    async def update_stock(self, product_id: str, quantity_change: int) -> Product:
        prod = await self.product_repo.get(self.db, product_id)
        if not prod:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found.")
        
        new_quantity = prod.stock_quantity + quantity_change
        if new_quantity < 0:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Insufficient stock.")
            
        prod.stock_quantity = new_quantity
        self.db.add(prod)
        await self.db.commit()
        await self.db.refresh(prod)
        return prod
